# StoryMemory Studio

**中文名：长篇记忆小说**

StoryMemory Studio is a local-first creative control center for long-form fiction and IP development. It combines a structured SQLite story memory database, long-context prompt orchestration, chapter generation, consistency checks, foreshadowing management, style profiling, AI-tone cleanup, and multi-format IP adaptation.

StoryMemory Studio 是一个本地优先的长篇小说与 IP 创作中控台。它不是“一键写小说”的玩具，而是把 **结构化记忆库 + 长上下文 Prompt 编排 + 章节生成 + 穿帮检测 + 文风学习 + AI 腔治理 + IP 改编** 放进同一个本地工作台。

> Built for web novel authors, short drama writers, comic adaptation creators, and anyone who has ever watched a long story slowly forget its own soul.

> 面向网文作者、短剧编剧、漫画改编创作者，以及所有被“写到后期设定忘光了”折磨过的人。

---

## Why StoryMemory Studio?

Long fiction does not fail because the model cannot write one chapter. It fails because the model forgets.

It forgets who knows what.  
It forgets which promise was made in chapter 12.  
It forgets that a character was injured, that a key changed hands, that a relationship had already broken once.  
It forgets the tone that made the opening work.

StoryMemory Studio treats memory as a first-class writing system:

- **SQLite is the source of truth** for facts, characters, relationships, rules, foreshadows, timelines, and logs.
- **Long-context LLMs are used deliberately**, not by dumping the whole novel into the prompt.
- **Context Builder ranks memory by priority**, so the next chapter sees what matters most.
- **Every generation is traceable**, reviewable, editable, and exportable.

长篇创作的问题通常不是模型写不出一章，而是它会忘。

它会忘记谁知道什么。  
它会忘记第 12 章埋过什么承诺。  
它会忘记某个角色受过伤、某把钥匙换过主人、某段关系已经裂过一次。  
它也会忘记开篇真正好看的那种语气。

StoryMemory Studio 把“记忆”当成创作系统的核心：

- **SQLite 是事实来源**：人物、关系、世界观规则、伏笔、时间线、章节事实都结构化保存。
- **长上下文能力谨慎使用**：不把全文粗暴塞进 Prompt，而是按优先级组织。
- **Context Builder 自动排序召回**：让下一章优先命中关键设定、人物、伏笔和前文事实。
- **所有生成都有日志**：可追踪、可编辑、可回滚、可导出。

---

## Highlights / 核心亮点

- **Local-first data safety**  
  Your projects, database, exports, and configuration live on your own machine.

- **Story Memory Engine**  
  Maintains structured long-term memory for characters, facts, foreshadows, rules, timelines, unresolved questions, and style profiles.

- **DeepSeek / OpenAI-compatible / Ollama support**  
  Use cloud APIs or local Ollama models. The default release flow prefers local Ollama when available.

- **Context Builder for long-context models**  
  Supports `lite 32k`, `standard 128k`, `deepseek_long 800k`, and `full_audit 1M` budget modes.

- **Create Novel Wizard**  
  Start from zero with a premise and generate a project Bible, character cards, world rules, foreshadows, timelines, first volume outline, first 10 chapter outlines, and first chapter draft.

- **Style Profiler**  
  Learn abstract style parameters from pasted or uploaded samples without copying protected text.

- **humanizer-zh built in**  
  Cleans model traces, template sentences, vague summaries, `<think>` remnants, and obvious AI-flavored prose after generation.

- **Novelization Rewriter**  
  Converts “setting explanation chapters” into more scene-driven fiction with action, subtext, friction, objects, and concrete hooks.

- **AI Tone Detector**  
  Separates real AI artifacts from acceptable light-novel expression and recommends local sentence fixes, paragraph rewriting, or full chapter polishing.

- **IP Adaptation Matrix**  
  Adapt chapters into comic storyboards, short drama scripts, video storyboards, Xiaohongshu posts, poster prompts, character cards, quotes, and teaser copy.

中文简述：

- 本地优先，数据默认保存在本机。
- 结构化维护人物、关系、伏笔、章节事实、时间线、世界观规则。
- 支持 DeepSeek、OpenAI-compatible 和 Ollama 本地模型。
- 针对百万 token 长上下文做分层 Prompt 编排。
- 支持从 0 创建小说项目。
- 支持导入已有作品并抽取长期记忆。
- 支持文风学习，但只提取抽象风格画像，不复制原文。
- 内置 `humanizer-zh`，生成后自动降低 AI 腔。
- 支持小说化重写，让章节从“设定说明”变成“场景推动”。
- 支持漫画、短剧、小红书、海报提示词等 IP 改编输出。

---

## Feature Map / 功能地图

### 1. Creation Launch / 创作启动

- Create Novel Wizard / 从 0 创建小说
- Project Manager / 项目管理
- Chapter Import / 章节导入

### 2. Memory Hub / 记忆中枢

- Memory Dashboard / 记忆库看板
- Memory Editor / 记忆编辑器
- Backup and Restore / 备份与恢复

### 3. Chapter Writing / 章节创作

- Chapter Generation / 章节生成
- Chapter Editing and Export / 章节编辑与导出
- Style Profiler / 文风学习器
- Model and Data Settings / 模型与数据设置

### 4. Consistency Management / 一致性管理

- Consistency Checker / 一致性检查
- Foreshadow Manager / 伏笔管理
- Timeline Manager / 时间线管理
- Character Arc Tracker / 人物弧光追踪

### 5. Quality Optimization / 质量优化

- AI Tone Detector / AI 腔检测
- Chapter Pacing Analyzer / 剧情节奏诊断
- Foreshadow Payoff Recommender / 伏笔回收推荐
- Platform Adapter / 平台适配器

### 6. IP Adaptation and Distribution / IP 改编与分发

- Adaptation Matrix / 章节改编矩阵
- Comic Storyboard / 漫画分镜
- Short Drama Script / 短剧脚本
- Xiaohongshu Post / 小红书文案
- Poster and Character Card Prompts / 海报与角色卡提示词

---

## Architecture / 架构概览

```text
User Input / Existing Chapters / Novel Seed
                |
                v
       Memory Extractor
                |
                v
 SQLite Story Memory Database
                |
                v
        Context Builder
   S / A / B / C / D priority layers
                |
                v
 LLM Provider: DeepSeek / OpenAI-compatible / Ollama
                |
                v
 Chapter Generator -> Output Cleaner -> humanizer-zh
                |
                v
 Consistency Checker / AI Tone Detector / Novelization Rewriter
                |
                v
 Memory Update + Logs + Export
```

核心原则：

1. **数据库是事实来源**，LLM 不是。
2. **长上下文用于全局理解和一致性推理**，不是拿来无脑塞全文。
3. **生成前构建上下文，生成后检查并更新记忆**。
4. **用户可以编辑所有关键创作资产**。
5. **所有 AI 输出都要可追踪**。

---

## Quick Start for Windows Users / Windows 用户快速启动

Download or build the release package, then double-click:

```text
StoryMemoryStudio.exe
```

First launch may take 10-30 seconds. The app opens a local browser page:

```text
http://127.0.0.1:8501
```

If the browser does not open, check:

```text
start_log.txt
```

中文：

进入发布包目录，双击：

```text
StoryMemoryStudio.exe
```

首次启动可能需要等待 10-30 秒。启动后会自动打开浏览器。如果没有打开，请查看 exe 同级目录的 `start_log.txt`。

---

## Release Folder / 发布包目录

```text
dist/
├── StoryMemoryStudio.exe
├── data/
├── exports/
├── prompts/
├── .env
├── .env.example
├── README.md
├── README_使用说明.md
├── schema.sql
└── start_log.txt
```

- `data/`: local SQLite database and project data
- `exports/`: exported docx, md, json files
- `prompts/`: prompt templates
- `.env`: model and path configuration
- `start_log.txt`: launcher logs

发布版不会把用户数据库写入 PyInstaller 临时目录，默认都保存在 exe 同级目录。

---

## Local Development / 开发模式

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run_ui.py
```

Run tests:

```powershell
python -m compileall app -q
python -m pytest -q
```

Current smoke test status:

```text
7 passed
```

---

## Model Setup / 模型配置

StoryMemory Studio supports:

- Ollama local models
- DeepSeek API
- OpenAI-compatible APIs
- OpenAI API

Default local configuration:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
DEFAULT_MODEL_PROVIDER=ollama
DEFAULT_OLLAMA_MODEL=auto
```

Recommended Ollama models:

```bash
ollama pull qwen3
ollama pull qwen2.5
ollama pull deepseek-r1
```

中文：

默认优先使用 Ollama 本地模型。也可以在“章节创作 / 模型与数据设置”里配置 DeepSeek 或 OpenAI-compatible API。

---

## Typical Workflow / 推荐工作流

### New Novel / 从 0 创建小说

1. Open `创作启动 / 从 0 创建小说`
2. Enter title, genre, platform, premise, protagonist, goal, selling points, avoid list, style reference
3. Generate a project Bible
4. Preview and edit characters, world rules, foreshadows, timeline, first 10 chapter outlines
5. Commit to Story Memory
6. Generate chapter one
7. Check consistency and AI tone
8. Continue chapter by chapter

中文：

1. 进入“创作启动 / 从 0 创建小说”
2. 填写标题、题材、平台、一句话设定、主角、目标、核心爽点、禁忌内容和文风参考
3. 生成小说 Bible
4. 预览并编辑人物、世界观、伏笔、时间线和前 10 章章纲
5. 确认写入 Story Memory
6. 生成第一章
7. 做一致性检查和 AI 腔检测
8. 继续生成后续章节

### Existing Novel / 导入已有作品

1. Create or select a project
2. Import txt, md, or docx chapters
3. Extract memory
4. Review the memory dashboard
5. Continue writing with Context Builder

中文：

1. 创建或选择项目
2. 导入 `txt/md/docx` 章节
3. 抽取记忆
4. 查看记忆库看板
5. 用 Context Builder 继续生成后续章节

---

## humanizer-zh Integration / 真人化处理

The MVP includes a local `humanizer-zh` module. It is called after chapter generation and during AI-tone repair / novelization rewriting.

It helps remove:

- `<think>` remnants
- English drafting traces
- prompt leakage
- template endings
- vague emotional summaries
- formulaic “not only X but Y” structures
- over-explained AI-style prose

It is conservative by design. It does **not** rewrite the plot wildly. It keeps story facts, character relationships, foreshadows, and chapter hooks intact.

中文：

当前版本已经内置 `humanizer-zh`。章节生成后会自动经过：

```text
LLM output -> output_cleaner -> humanizer-zh -> save/export
```

AI 腔润色和小说化重写也会调用同一套逻辑。它主要清理模型痕迹、模板句、英文草稿、空泛总结和提示词残留，不会大幅改剧情。

---

## Export / 导出

Supported exports:

- Single chapter: `txt`, `md`, `docx`, `json`
- Full project: `docx`
- Story Bible: `world_bible.md`, `character_bible.md`, `outline.md`, `timeline.md`, `foreshadows.md`
- Style profile: `json`, `md`, prompt rules
- Adaptation outputs: `json`, `markdown`

导出文件默认在：

```text
exports/
```

---

## Build Windows EXE / 打包 Windows 可执行文件

```powershell
python build_exe.py
```

Output:

```text
dist/StoryMemoryStudio.exe
```

`build_exe.py` collects Streamlit resources, prompt templates, schema, README, and required app modules. It also creates runtime folders such as `data/` and `exports/`.

---

## CLI Examples / CLI 示例

```powershell
python -m app.cli init --name demo --title 我的小说
python -m app.cli import-chapter demo ./chapter1.txt --number 1 --title 第一章 --provider none
python -m app.cli build-context demo 2 --goal 推进主线 --mode standard
python -m app.cli detect-ai-tone --project-id 1 --chapter-id 1
python -m app.cli novelize-chapter --project-id 1 --chapter-id 1 --save-as-new-version true
python -m app.cli adapt-chapter --project-id 1 --chapter-id 1 --type all
```

---

## Data Safety / 数据安全

StoryMemory Studio is local-first:

- No project data is uploaded by default.
- SQLite database stays in `data/`.
- Exported documents stay in `exports/`.
- `.env` is ignored by git.
- User data folders are ignored by git.

中文：

默认不上传用户作品数据。数据库、导出文件和配置都保存在本地。`.gitignore` 已排除 `.env`、`data/`、`exports/`、`backups/`、`dist/` 和 `.venv/`。

---

## Known TODO / 当前 TODO

- Legacy `.doc` import depends on system environment; `txt/md/docx` are the stable paths.
- Release package does not yet include installer, tray exit, or code signing.
- Advanced quality modules have working MVP flows; future versions can add benchmark datasets and richer evaluation.

---

## Suggested Repository Description

**A local-first AI writing control center for long-form fiction: structured story memory, long-context prompt orchestration, consistency checks, AI-tone cleanup, and IP adaptation.**

中文一句话：

**一个本地优先的长篇小说 AI 创作中控台：结构化记忆、长上下文编排、一致性检查、AI 腔治理与 IP 改编。**

