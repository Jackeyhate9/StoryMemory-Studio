from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.checkers.consistency import ConsistencyChecker
from app.config import get_settings
from app.context.builder import ContextBuilder
from app.creation.wizard import commit_preview, create_preview_from_kwargs
from app.db.database import db_session, get_project, init_db, log_generation
from app.db.models import ContextRequest
from app.acceptance_e2e import run_rose_mansion_e2e
from app.export.bible_export import export_bible as run_export_bible
from app.export.docx_export import export_project_docx
from app.export.json_export import export_project_json
from app.export.markdown import export_project_markdown
from app.generation.chapter import generate_chapter as run_generate_chapter
from app.generation.outline import generate_outline as run_generate_outline
from app.llm.client import get_llm
from app.llm.ollama_utils import select_best_ollama_model
from app.llm.validation import validate_llm_connection
from app.quality.batch_polish import polish_ai_tone_batch
from app.quality.novelization_rewriter import novelize_chapter, novelize_project
from app.memory.extractor import MemoryExtractor
from app.memory.writer import upsert_extraction
from app.ui.services import create_backup, list_backups
from app.style.profiler import analyze_style
from app.style.similarity_guard import check_similarity
from app.style.style_safety import read_style_file
from app.style.style_schema import StyleProfileInput
from app.style.style_store import export_style_profile, get_style_profile_by_id, get_style_samples, save_style_profile
from app.creative_center import (
    adapt_chapter_for_ip,
    adapt_platform_for_chapter,
    analyze_character_arc_for_project,
    analyze_pacing_for_chapter,
    analyze_platform_fit_for_chapter,
    character_presence_for_project,
    detect_ai_tone_for_chapter,
    detect_character_drift_for_chapter,
    plan_payoff_for_foreshadow,
    recommend_payoff_for_project,
    rewrite_ai_tone_for_chapter,
)

app = typer.Typer(help="StoryMemory Studio - 长篇小说结构化记忆创作中控台")
console = Console()


def print_json_safe(value) -> None:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            text = json.dumps(parsed, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            text = value
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def _client_or_none(provider: str | None):
    if provider == "none":
        return None
    return get_llm(provider) if provider else None


def _truthy(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "是", "保存"}


@app.command()
def init(
    name: str = typer.Option("demo", help="项目标识"),
    title: str = typer.Option("长篇记忆小说", help="作品标题"),
    description: str = typer.Option("", help="项目简介"),
    genre: str = typer.Option("", help="类型"),
    platform: str = typer.Option("", help="目标平台"),
):
    """初始化数据库并创建小说项目。"""
    path = init_db()
    with db_session(path) as conn:
        conn.execute(
            """
            INSERT INTO projects (name, title, description, genre, target_platform)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
              title=excluded.title, description=excluded.description, genre=excluded.genre,
              target_platform=excluded.target_platform, updated_at=CURRENT_TIMESTAMP
            """,
            (name, title, description, genre, platform),
        )
    console.print(f"[green]OK[/green] 数据库已初始化：{path}")


@app.command("import-chapter")
def import_chapter(
    project: str,
    file: Path,
    number: int = typer.Option(..., help="章节序号"),
    title: str = typer.Option("", help="章节标题，默认取文件名"),
    volume: str = typer.Option("", help="卷名"),
    provider: str = typer.Option("none", help="deepseek/openai/openai_compatible/ollama/none"),
):
    """导入章节，并自动抽取 summary、facts、人物、伏笔、时间线。"""
    init_db()
    content = file.read_text(encoding="utf-8")
    chapter_title = title or file.stem
    with db_session() as conn:
        p = get_project(conn, project)
        conn.execute(
            """
            INSERT INTO chapters (project_id, chapter_number, volume, title, content, word_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, chapter_number) DO UPDATE SET
              volume=excluded.volume, title=excluded.title, content=excluded.content,
              word_count=excluded.word_count, updated_at=CURRENT_TIMESTAMP
            """,
            (p["id"], number, volume, chapter_title, content, len(content)),
        )
        chapter_id = conn.execute(
            "SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?", (p["id"], number)
        ).fetchone()["id"]
        extractor = MemoryExtractor(_client_or_none(provider))
        extraction = extractor.extract(chapter_title, content)
        upsert_extraction(conn, p["id"], chapter_id, extraction)
        log_generation(
            conn,
            p["id"],
            "import_chapter_extract_memory",
            provider=provider,
            response=extraction.model_dump_json(),
            structured=extraction.model_dump(),
            chapter_id=chapter_id,
        )
    console.print(f"[green]OK[/green] 已导入并抽取记忆：第 {number} 章《{chapter_title}》")


@app.command("extract-memory")
def extract_memory(project: str, chapter_number: int, provider: str = typer.Option("none")):
    """对已导入章节重新抽取结构化记忆。"""
    with db_session() as conn:
        p = get_project(conn, project)
        chapter = conn.execute(
            "SELECT * FROM chapters WHERE project_id = ? AND chapter_number = ?", (p["id"], chapter_number)
        ).fetchone()
        if not chapter:
            raise typer.BadParameter("chapter not found")
        extractor = MemoryExtractor(_client_or_none(provider))
        extraction = extractor.extract(chapter["title"], chapter["content"])
        upsert_extraction(conn, p["id"], chapter["id"], extraction)
        log_generation(
            conn,
            p["id"],
            "extract_memory",
            provider=provider,
            response=extraction.model_dump_json(),
            structured=extraction.model_dump(),
            chapter_id=chapter["id"],
        )
    console.print("[green]OK[/green] 记忆已更新")


@app.command("build-context")
def build_context(
    project: str,
    chapter_number: int,
    goal: str = typer.Option("", help="当前章节目标"),
    outline: str = typer.Option("", help="当前章节大纲"),
    characters: str = typer.Option("", help="逗号分隔人物"),
    locations: str = typer.Option("", help="逗号分隔地点"),
    plot_threads: str = typer.Option("", help="逗号分隔剧情线"),
    mode: str = typer.Option("standard", help="lite/standard/deepseek_long/full_audit"),
    output: Path | None = typer.Option(None),
):
    """按优先级构建 DeepSeek 长上下文友好的 Prompt。"""
    with db_session() as conn:
        p = get_project(conn, project)
        req = ContextRequest(
            project=project,
            chapter_number=chapter_number,
            chapter_goal=goal,
            chapter_outline=outline,
            characters=[x.strip() for x in characters.split(",") if x.strip()],
            locations=[x.strip() for x in locations.split(",") if x.strip()],
            plot_threads=[x.strip() for x in plot_threads.split(",") if x.strip()],
            mode=mode,  # type: ignore[arg-type]
        )
        prompt = ContextBuilder(conn, p).build(req)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(prompt, encoding="utf-8")
        console.print(f"[green]OK[/green] 已写入 {output}")
    else:
        console.print(prompt)


@app.command("generate-outline")
def generate_outline(project: str, chapter_number: int, goal: str, outline: str = "", provider: str | None = None):
    """调用 LLM 生成章节大纲。"""
    with db_session() as conn:
        p = get_project(conn, project)
        req = ContextRequest(project=project, chapter_number=chapter_number, chapter_goal=goal, chapter_outline=outline)
        context = ContextBuilder(conn, p).build(req)
        client = get_llm(provider)
        text = run_generate_outline(client, context)
        log_generation(conn, p["id"], "generate_outline", client.provider, client.model, context, text)
    console.print(text)


@app.command("generate-chapter")
def generate_chapter(
    project: str,
    chapter_number: int,
    goal: str,
    outline: str = "",
    provider: str | None = None,
    output: Path | None = None,
):
    """调用 LLM 生成章节正文，并自动运行一致性检查。"""
    with db_session() as conn:
        p = get_project(conn, project)
        req = ContextRequest(project=project, chapter_number=chapter_number, chapter_goal=goal, chapter_outline=outline)
        context = ContextBuilder(conn, p).build(req)
        client = get_llm(provider)
        text = run_generate_chapter(client, context)
        report = ConsistencyChecker(client).check(context, text, goal)
        log_generation(
            conn,
            p["id"],
            "generate_chapter",
            client.provider,
            client.model,
            context,
            text,
            {"consistency": report.model_dump()},
        )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        console.print(f"[green]OK[/green] 正文已写入 {output}")
    else:
        console.print(text)
    if not report.passed:
        console.print("[red]一致性检查发现问题：[/red]")
        print_json_safe(report.model_dump())


@app.command("check-consistency")
def check_consistency(
    project: str,
    chapter_file: Path,
    chapter_number: int = typer.Option(..., help="章节序号"),
    goal: str = "",
    provider: str = typer.Option("none"),
):
    """检查章节是否穿帮、违背硬设定或出现 AI 腔。"""
    text = chapter_file.read_text(encoding="utf-8")
    with db_session() as conn:
        p = get_project(conn, project)
        context = ContextBuilder(conn, p).build(ContextRequest(project=project, chapter_number=chapter_number, chapter_goal=goal))
        checker = ConsistencyChecker(_client_or_none(provider))
        report = checker.check(context, text, goal)
    print_json_safe(report.model_dump())


@app.command("list-foreshadows")
def list_foreshadows(project: str):
    """列出伏笔状态。"""
    with db_session() as conn:
        p = get_project(conn, project)
        rows = conn.execute("SELECT * FROM foreshadows WHERE project_id = ? ORDER BY status, id", (p["id"],)).fetchall()
    table = Table("ID", "名称", "状态", "预计回收", "风险")
    for row in rows:
        table.add_row(str(row["id"]), row["name"], row["status"], str(row["expected_resolution_chapter"] or ""), row["risk_note"] or "")
    console.print(table)


@app.command("update-foreshadow")
def update_foreshadow(project: str, foreshadow_id: int, status: str, resolution: str = ""):
    """更新伏笔状态和回收方式。"""
    with db_session() as conn:
        p = get_project(conn, project)
        conn.execute(
            "UPDATE foreshadows SET status = ?, resolution_method = COALESCE(NULLIF(?, ''), resolution_method) WHERE project_id = ? AND id = ?",
            (status, resolution, p["id"], foreshadow_id),
        )
    console.print("[green]OK[/green] 伏笔已更新")


@app.command("export-memory")
def export_memory(project: str, output: Path, format: str = typer.Option("json", help="json/markdown")):
    """导出可备份、可人工编辑的记忆文件。"""
    with db_session() as conn:
        p = get_project(conn, project)
        if format == "json":
            path = export_project_json(conn, p["id"], output)
        else:
            path = export_project_markdown(conn, p["id"], output)
    console.print(f"[green]OK[/green] 已导出 {path}")


@app.command("test-llm")
def test_llm(
    provider: str = typer.Option("deepseek", help="deepseek/openai/openai_compatible/ollama"),
    no_completion: bool = typer.Option(False, help="Only check model listing endpoint"),
):
    """Validate configured LLM provider, model listing, selected model, and chat completion."""
    result = validate_llm_connection(provider, run_completion=not no_completion)
    if result["ok"]:
        console.print("[green]OK[/green] LLM connection validated")
    else:
        console.print("[red]FAILED[/red] LLM connection validation failed or is incomplete")
    print_json_safe(result)


@app.command("backup")
def backup(note: str = typer.Option("", help="Short backup note")):
    """Create a local zip backup of the SQLite database and editable exports."""
    path = create_backup(note)
    console.print(f"[green]OK[/green] Backup created: {path}")


@app.command("list-backups")
def list_backup_files():
    """List local backup zip files."""
    rows = list_backups()
    table = Table("Name", "Size KB", "Path")
    for row in rows:
        table.add_row(row["name"], str(row["size_kb"]), row["path"])
    console.print(table)


@app.command("create-novel")
def create_novel(
    mode: str = typer.Option("minimal", help="minimal/pro"),
    title: str = typer.Option(...),
    genre: str = typer.Option(""),
    platform: str = typer.Option(""),
    premise: str = typer.Option(""),
    protagonist: str = typer.Option(""),
    goal: str = typer.Option(""),
    selling_points: str = typer.Option(""),
    avoid: str = typer.Option(""),
    length: str = typer.Option("100章"),
    style: str = typer.Option(""),
    target_reader: str = typer.Option(""),
    word_count: int = typer.Option(0),
    output_project: str = typer.Option(""),
    provider: str = typer.Option("none", help="none/deepseek/openai/openai_compatible/ollama"),
    yes: bool = typer.Option(False, help="Commit without asking"),
):
    """Create a new novel from zero, save preview, and optionally commit it into Story Memory."""
    preview = create_preview_from_kwargs(
        provider=provider,
        mode=mode,
        title=title,
        genre=genre,
        platform=platform,
        premise=premise,
        protagonist=protagonist,
        goal=goal,
        selling_points=selling_points,
        avoid=avoid,
        length=length,
        style=style,
        target_reader=target_reader,
        word_count=word_count,
    )
    result = preview["result"]
    preview_path = preview["preview_path"]
    console.print(f"[green]OK[/green] Preview saved: {preview_path}")
    console.print(f"Title: {result.project.title}")
    console.print(f"Logline: {result.project.logline}")
    console.print(f"Characters: {', '.join([c.name for c in result.characters])}")
    console.print(f"First chapter: {result.first_chapter.title}")
    if yes or typer.confirm("确认写入 Story Memory 数据库？"):
        committed = commit_preview(preview_path, output_project or None, provider)
        console.print(f"[green]OK[/green] Project committed: {committed['project']}")
        console.print("Second chapter context preview:")
        console.print(committed["second_chapter_context"][:3000])
    else:
        console.print("已保留 preview，未写入正式数据库。")


@app.command("export-bible")
def export_bible(
    project: str = typer.Option(..., help="Project name"),
    output: Path = typer.Option(Path("./exports"), help="Output directory"),
):
    """Export world bible, character bible, outline, foreshadows, timeline, first chapter, and JSON memory."""
    with db_session() as conn:
        p = get_project(conn, project)
        path = run_export_bible(conn, p["id"], output)
    console.print(f"[green]OK[/green] Bible exported: {path}")


@app.command("export-docx")
def export_docx(
    project_id: int = typer.Option(..., help="Project id"),
    output: Path = typer.Option(Path("./exports/storymemory_export.docx"), help="Output docx path"),
    model_name: str = typer.Option("", help="Model name written to the cover page"),
):
    """Export a complete project manuscript and memory appendix as docx."""
    init_db()
    with db_session() as conn:
        path = export_project_docx(conn, project_id, output, model_name=model_name)
    console.print(f"[green]OK[/green] DOCX exported: {path}")


@app.command("test-generate-novel")
def test_generate_novel(
    title: str = typer.Option("玫瑰大厦", help="Novel title"),
    chapters: int = typer.Option(10, help="Number of chapters to generate"),
    words_per_chapter: int = typer.Option(3000, help="Target length per chapter"),
    model_provider: str = typer.Option("ollama", help="Only ollama is used by this acceptance command"),
    ollama_model: str = typer.Option("auto", help="auto or a local Ollama model name"),
    auto_select_model: bool = typer.Option(True, help="Auto-select the best local Ollama model"),
    export_docx_file: bool = typer.Option(True, "--export-docx/--no-export-docx", help="Export docx after generation"),
    export_report: bool = typer.Option(False, help="Accepted for compatibility; reports are printed as JSON"),
    output: Path = typer.Option(Path("exports/玫瑰大厦_10章测试版.docx"), help="DOCX output path"),
    keep_existing: bool = typer.Option(False, help="Do not delete an existing project with the same title before testing"),
):
    """Run the full local Ollama acceptance flow: create bible, generate chapters, update memory, export docx."""
    if ollama_model != "auto":
        console.print("[yellow]当前验收命令已接收 --ollama-model，但自动选型仍以本地模型优先级为准。[/yellow]")
    if model_provider != "ollama":
        raise typer.BadParameter("本验收命令按用户要求只使用本地 Ollama，请设置 --model-provider ollama")
    if auto_select_model:
        selection = select_best_ollama_model()
        if not selection.available or not selection.model:
            print_json_safe(selection.model_dump())
            raise typer.Exit(code=2)
        console.print(f"[green]Ollama 可用[/green]，自动选择模型：{selection.model}")
    report = run_rose_mansion_e2e(
        title=title,
        chapters=chapters,
        words_per_chapter=words_per_chapter,
        output_docx=(Path("exports") / f"{title}_10章测试版.docx") if export_docx_file and str(output) == "exports\\玫瑰大厦_10章测试版.docx" and title != "玫瑰大厦" else (output if export_docx_file else None),
        reset=not keep_existing,
    )
    if export_report:
        safe_title = "".join(ch for ch in title if ch not in '\\/:*?"<>|')
        report_json = Path("exports") / f"{safe_title}_测试报告.json"
        report_md = Path("exports") / f"{safe_title}_测试报告.md"
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        md = [
            f"# {title} 端到端测试报告",
            "",
            f"- 项目 ID：{report.get('project_id')}",
            f"- 使用模型：{report.get('ollama', {}).get('model')}",
            f"- 章节数：{len(report.get('chapter_stats', []))}",
            f"- DOCX：{report.get('docx_path')}",
            f"- Story Memory：{report.get('counts')}",
        ]
        report_md.write_text("\n".join(md), encoding="utf-8")
        report["test_report_json_path"] = str(report_json)
        report["test_report_md_path"] = str(report_md)
    print_json_safe(report)


@app.command("analyze-style")
def analyze_style_cmd(
    project: str = typer.Option(..., help="Project name"),
    style_name: str = typer.Option(...),
    sample_file: Path = typer.Option(...),
    target_usage: str = typer.Option("novel_chapter"),
    save_source: str = typer.Option("false", help="true/false"),
    set_default: str = typer.Option("false", help="true/false"),
    provider: str = typer.Option("none", help="none/deepseek/openai/openai_compatible/ollama"),
):
    """Analyze sample writing into an abstract style profile and save it to project."""
    save_source_bool = _truthy(save_source)
    set_default_bool = _truthy(set_default)
    sample = read_style_file(sample_file)
    input_data = StyleProfileInput(style_name=style_name, samples=[sample], target_usage=[target_usage], source_note=str(sample_file), save_source=save_source_bool, set_default=set_default_bool)
    profile = analyze_style(input_data, provider)
    style_id = save_style_profile(project, profile, [sample], str(sample_file), save_source_bool, set_default_bool)
    console.print(f"[green]OK[/green] Style profile saved: {style_id}")
    print_json_safe(profile.model_dump())


@app.command("check-style-similarity")
def check_style_similarity_cmd(
    style_profile_id: int = typer.Option(..., help="Style profile id"),
    generated_file: Path = typer.Option(..., help="Generated text file"),
):
    """Check generated text against stored safe excerpts/full samples for similarity risk."""
    generated = generated_file.read_text(encoding="utf-8-sig")
    samples = get_style_samples(style_profile_id)
    combined = "\n\n".join([(s.get("sample_text") or s.get("sample_excerpt_safe") or "") for s in samples])
    report = check_similarity(combined, generated)
    print_json_safe(report.model_dump())


@app.command("apply-style")
def apply_style_cmd(
    style_profile_id: int = typer.Option(..., help="Style profile id"),
    input_file: Path = typer.Option(..., help="Input text file"),
    output_file: Path = typer.Option(..., help="Output text file"),
    provider: str = typer.Option("none", help="none/deepseek/openai/openai_compatible/ollama"),
):
    """Rewrite text with abstract style rules, never by copying the source sample."""
    profile = get_style_profile_by_id(style_profile_id)
    if not profile:
        raise typer.BadParameter("style profile not found")
    text = input_file.read_text(encoding="utf-8-sig")
    output_text = text
    if provider != "none":
        template = (Path(__file__).parent / "prompts" / "style_transfer_rewrite.md").read_text(encoding="utf-8")
        prompt = template.format(
            context="CLI style rewrite",
            memory="Use only the provided abstract style profile.",
            style_profile=profile.get("safe_style_summary") or profile.get("profile_json") or "",
            user_goal="Rewrite the input as original text using only abstract style parameters.",
            text=text,
        )
        output_text = get_llm(provider).complete(prompt, system="你是原创润色助手，只能迁移抽象风格，不能复用样章表达。")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(output_text, encoding="utf-8")
    console.print(f"[green]OK[/green] Wrote styled draft: {output_file}")


@app.command("detect-ai-tone")
def detect_ai_tone_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...)):
    """Detect AI-like wording and template prose in a chapter."""
    init_db()
    print_json_safe(detect_ai_tone_for_chapter(project_id, chapter_id))


@app.command("rewrite-ai-tone")
def rewrite_ai_tone_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...), apply: str = typer.Option("false")):
    """Create a naturalized rewrite while preserving the original chapter."""
    init_db()
    print_json_safe(rewrite_ai_tone_for_chapter(project_id, chapter_id, _truthy(apply)))


@app.command("analyze-pacing")
def analyze_pacing_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...)):
    """Analyze chapter pacing, hook, conflict, emotion peak, and retention."""
    init_db()
    print_json_safe(analyze_pacing_for_chapter(project_id, chapter_id))


@app.command("improve-pacing")
def improve_pacing_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...), apply: str = typer.Option("false")):
    """Return pacing improvement directions. Applying full rewrite is reserved for LLM mode."""
    init_db()
    report = analyze_pacing_for_chapter(project_id, chapter_id)
    payload = {"apply": _truthy(apply), "report": report, "directions": ["强爽点版", "强悬疑版", "强情绪版"]}
    print_json_safe(payload)


@app.command("recommend-payoff")
def recommend_payoff_cmd(project_id: int = typer.Option(...)):
    """Recommend foreshadow payoff windows."""
    init_db()
    print_json_safe(recommend_payoff_for_project(project_id))


@app.command("plan-payoff")
def plan_payoff_cmd(project_id: int = typer.Option(...), foreshadow_id: int = typer.Option(...)):
    """Generate a payoff plan for one foreshadow."""
    init_db()
    print_json_safe(plan_payoff_for_foreshadow(project_id, foreshadow_id))


@app.command("analyze-character-arc")
def analyze_character_arc_cmd(project_id: int = typer.Option(...), character_id: int = typer.Option(...)):
    """Analyze one character's arc state."""
    init_db()
    print_json_safe(analyze_character_arc_for_project(project_id, character_id))


@app.command("detect-character-drift")
def detect_character_drift_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...)):
    """Detect character drift for a chapter."""
    init_db()
    print_json_safe(detect_character_drift_for_chapter(project_id, chapter_id))


@app.command("list-character-presence")
def list_character_presence_cmd(project_id: int = typer.Option(...)):
    """List character presence summary."""
    init_db()
    print_json_safe(character_presence_for_project(project_id))


@app.command("analyze-platform-fit")
def analyze_platform_fit_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...), platform: str = typer.Option(...)):
    """Analyze chapter fit for a target platform."""
    init_db()
    print_json_safe(analyze_platform_fit_for_chapter(project_id, chapter_id, platform))


@app.command("adapt-platform")
def adapt_platform_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...), platform: str = typer.Option(...), apply: str = typer.Option("false")):
    """Create a platform-adapted version while preserving the original chapter."""
    init_db()
    print_json_safe(adapt_platform_for_chapter(project_id, chapter_id, platform, _truthy(apply)))


@app.command("adapt-chapter")
def adapt_chapter_cmd(project_id: int = typer.Option(...), chapter_id: int = typer.Option(...), type: str = typer.Option("all")):
    """Adapt a chapter into comic, short drama, video, xiaohongshu, poster, quotes, or all."""
    init_db()
    print_json_safe(adapt_chapter_for_ip(project_id, chapter_id, type))


@app.command("polish-ai-tone-batch")
def polish_ai_tone_batch_cmd(
    project_id: int = typer.Option(...),
    mode: str = typer.Option("chapter_polish", help="local_sentence_rewrite/paragraph_rewrite/chapter_polish"),
    save_as_new_version: str = typer.Option("true", help="true/false"),
    export_docx: str = typer.Option("true", help="true/false"),
):
    """Batch-detect and naturally polish AI-tone issues, preserving original chapters."""
    init_db()
    report = polish_ai_tone_batch(
        project_id=project_id,
        mode=mode,
        save_as_new_version=_truthy(save_as_new_version),
        export_docx=_truthy(export_docx),
    )
    print_json_safe(report)


@app.command("novelize-chapter")
def novelize_chapter_cmd(
    project_id: int = typer.Option(...),
    chapter_id: int = typer.Option(...),
    save_as_new_version: str = typer.Option("true", help="true/false"),
    export_docx: str = typer.Option("true", help="true/false"),
):
    """Rewrite one chapter from exposition-heavy prose into scene-driven novel prose."""
    init_db()
    report = novelize_chapter(project_id, chapter_id, _truthy(save_as_new_version))
    if _truthy(export_docx):
        from app.export.docx_export import export_project_docx

        with db_session() as conn:
            path = export_project_docx(conn, project_id, Path("exports") / "novelized_chapter_export.docx", "novelization_rewriter")
        report["docx_path"] = str(path)
    print_json_safe(report)


@app.command("novelize-project")
def novelize_project_cmd(
    project_id: int = typer.Option(...),
    save_as_new_version: str = typer.Option("true", help="true/false"),
    export_docx: str = typer.Option("true", help="true/false"),
):
    """Rewrite a whole project into scene-driven, show-not-tell novel prose."""
    init_db()
    report = novelize_project(project_id, _truthy(save_as_new_version), _truthy(export_docx))
    print_json_safe(report)


if __name__ == "__main__":
    app()
