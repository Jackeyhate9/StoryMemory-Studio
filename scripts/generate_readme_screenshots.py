from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
    Path(r"C:\Windows\Fonts\arial.ttf"),
]
FONT_PATH = next((p for p in FONT_CANDIDATES if p.exists()), None)


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if FONT_PATH:
        return ImageFont.truetype(str(FONT_PATH), size)
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def shadow_card(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int = 16) -> None:
    x1, y1, x2, y2 = xy
    rounded(draw, (x1 + 3, y1 + 5, x2 + 3, y2 + 5), radius, (220, 226, 235))
    rounded(draw, xy, radius, (255, 255, 255), (222, 226, 233))


def sidebar(draw: ImageDraw.ImageDraw, active_section: str, active_page: str) -> None:
    draw.rectangle((0, 0, 285, 930), fill=(248, 250, 252))
    draw.text((28, 26), "StoryMemory", font=font(25), fill=(24, 33, 47))
    draw.text((30, 60), "Studio 长篇记忆小说", font=font(13), fill=(100, 116, 139))
    y = 110
    sections = [
        ("创作启动", "从 0 创建小说"),
        ("记忆中枢", "记忆库看板"),
        ("章节创作", "章节生成"),
        ("一致性管理", "一致性检查"),
        ("质量优化", "AI 腔检测"),
        ("IP 改编与分发", "章节改编矩阵"),
    ]
    for section, page in sections:
        active = section == active_section
        if active:
            rounded(draw, (20, y - 8, 265, y + 38), 12, (225, 232, 246))
        draw.text((34, y), section, font=font(17), fill=(30, 41, 59) if active else (91, 103, 122))
        draw.text((48, y + 36), page, font=font(14), fill=(37, 99, 235) if active else (120, 130, 145))
        y += 82


def header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.text((330, 38), title, font=font(34), fill=(15, 23, 42))
    draw.text((332, 88), subtitle, font=font(16), fill=(100, 116, 139))


def dashboard() -> None:
    img = Image.new("RGB", (1440, 930), (241, 245, 249))
    draw = ImageDraw.Draw(img)
    sidebar(draw, "创作启动", "从 0 创建小说")
    header(draw, "StoryMemory Studio", "SQL 结构化记忆库 + 长上下文 Prompt 编排器 + 长篇小说创作中控台")

    stats = [("当前项目", "玫瑰大厦"), ("章节", "10"), ("人物卡", "14"), ("未回收伏笔", "9")]
    x = 330
    for label, value in stats:
        shadow_card(draw, (x, 130, x + 235, 220))
        draw.text((x + 22, 150), label, font=font(14), fill=(100, 116, 139))
        draw.text((x + 22, 178), value, font=font(26), fill=(15, 23, 42))
        x += 260

    cards = [
        ("创作启动", "从零创建小说、导入已有章节、管理项目。", "从 0 创建小说 / 项目管理 / 章节导入"),
        ("记忆中枢", "人物、伏笔、时间线、世界观规则沉淀为可编辑数据库。", "记忆库看板 / 记忆编辑器 / 备份恢复"),
        ("章节创作", "构建上下文、生成章节、编辑导出、接入文风画像。", "章节生成 / 文风学习器 / 模型设置"),
        ("质量优化", "检测 AI 腔、诊断节奏、平台适配和伏笔回收。", "AI 腔检测 / 剧情节奏 / 平台适配"),
    ]
    for (title, desc, items), (x, y) in zip(cards, [(330, 265), (815, 265), (330, 505), (815, 505)]):
        shadow_card(draw, (x, y, x + 445, y + 185))
        draw.text((x + 24, y + 24), title, font=font(23), fill=(15, 23, 42))
        draw.text((x + 24, y + 65), desc, font=font(15), fill=(71, 85, 105))
        draw.text((x + 24, y + 108), items, font=font(14), fill=(37, 99, 235))
        rounded(draw, (x + 24, y + 138, x + 120, y + 168), 10, (37, 99, 235))
        draw.text((x + 54, y + 143), "进入", font=font(14), fill=(255, 255, 255))

    shadow_card(draw, (330, 735, 1340, 890))
    draw.text((360, 760), "技术架构", font=font(22), fill=(15, 23, 42))
    tech = "SQLite / SQLAlchemy / Pydantic / Streamlit / Typer / Rich / httpx / Ollama / DeepSeek / python-docx / PyInstaller"
    draw.text((360, 803), tech, font=font(16), fill=(37, 99, 235))
    draw.text((360, 837), "本地结构化记忆库 + DeepSeek 百万 token 长上下文编排 + AI 腔治理 + IP 改编导出", font=font(15), fill=(71, 85, 105))
    img.save(OUT / "dashboard.png")


def context_builder() -> None:
    img = Image.new("RGB", (1440, 930), (241, 245, 249))
    draw = ImageDraw.Draw(img)
    sidebar(draw, "章节创作", "章节生成")
    header(draw, "章节生成", "按 S/A/B/C/D 优先级构建上下文，不把全书粗暴塞进 Prompt。")
    shadow_card(draw, (330, 135, 665, 820))
    draw.text((360, 165), "生成设置", font=font(22), fill=(15, 23, 42))
    labels = ["本章目标", "本章大纲", "上下文预算", "模型提供方", "文风画像"]
    values = ["推进继承权暗线", "晚宴后，旧账本浮出水面", "deepseek_long 800k", "Ollama / DeepSeek / OpenAI", "现代都市轻小说"]
    y = 215
    for label, value in zip(labels, values):
        draw.text((360, y), label, font=font(14), fill=(100, 116, 139))
        rounded(draw, (360, y + 24, 625, y + 70), 10, (248, 250, 252), (203, 213, 225))
        draw.text((378, y + 38), value, font=font(13), fill=(51, 65, 85))
        y += 92
    rounded(draw, (360, 705, 510, 748), 12, (37, 99, 235))
    draw.text((390, 716), "构建上下文", font=font(15), fill=(255, 255, 255))

    shadow_card(draw, (700, 135, 1340, 820))
    draw.text((730, 165), "Context Preview", font=font(22), fill=(15, 23, 42))
    blocks = [
        ("S 当前任务强相关", "当前章节目标、出场人物完整人物卡、相关伏笔、上一章事实"),
        ("A 必须遵守硬设定", "世界观硬规则、禁止违背规则、时间线关键节点"),
        ("B 长线辅助信息", "主线剧情、人物关系变化、未解决问题、道具状态"),
        ("C 风格与平台适配", "文风画像、反 AI 腔规则、平台节奏、对话风格"),
        ("D 压缩背景信息", "早期章节摘要树、全书总纲、历史归档信息"),
    ]
    colors = [(219, 234, 254), (220, 252, 231), (254, 249, 195), (243, 232, 255), (226, 232, 240)]
    y = 215
    for (title, body), color in zip(blocks, colors):
        rounded(draw, (730, y, 1305, y + 75), 12, color, (203, 213, 225))
        draw.text((750, y + 12), title, font=font(16), fill=(15, 23, 42))
        draw.text((750, y + 40), body, font=font(13), fill=(71, 85, 105))
        y += 93
    img.save(OUT / "context-builder.png")


def ai_tone() -> None:
    img = Image.new("RGB", (1440, 930), (241, 245, 249))
    draw = ImageDraw.Draw(img)
    sidebar(draw, "质量优化", "AI 腔检测")
    header(draw, "AI 腔检测与小说化重写", "区分真正严重问题、轻小说可保留表达，并给出可执行修复。")
    shadow_card(draw, (330, 135, 615, 300))
    draw.text((360, 165), "总风险", font=font(17), fill=(100, 116, 139))
    draw.text((360, 205), "Medium", font=font(38), fill=(217, 119, 6))
    draw.text((360, 255), "建议：段落级自然化润色", font=font(15), fill=(71, 85, 105))
    shadow_card(draw, (645, 135, 1340, 300))
    draw.text((675, 165), "问题分布", font=font(20), fill=(15, 23, 42))
    y = 205
    for name, value in [("人物设定卡插入", 62), ("对白解释剧情", 48), ("模板化钩子", 35), ("可保留轻小说表达", 20)]:
        draw.text((675, y), name, font=font(14), fill=(71, 85, 105))
        rounded(draw, (860, y + 3, 1270, y + 19), 8, (226, 232, 240))
        rounded(draw, (860, y + 3, 860 + value * 4, y + 19), 8, (37, 99, 235))
        y += 28

    shadow_card(draw, (330, 335, 1340, 790))
    draw.text((360, 365), "推荐修复动作", font=font(22), fill=(15, 23, 42))
    x = 360
    for action in ["只修明显 AI 腔句子", "润色问题段落", "整章自然化", "小说化重写本章", "导出小说化 docx"]:
        active = action == "小说化重写本章"
        rounded(draw, (x, 410, x + 170, 452), 12, (37, 99, 235) if active else (255, 255, 255), (203, 213, 225))
        draw.text((x + 18, 422), action, font=font(13), fill=(255, 255, 255) if active else (51, 65, 85))
        x += 185

    rounded(draw, (360, 490, 1290, 570), 12, (254, 242, 242), (254, 202, 202))
    draw.text((385, 512), "必须修复", font=font(16), fill=(153, 27, 27))
    draw.text((480, 512), "“她的眼神中闪过复杂的情绪。”  →  改为动作、停顿、物件和潜台词。", font=font(15), fill=(71, 85, 105))
    rounded(draw, (360, 600, 1290, 690), 12, (240, 253, 244), (187, 247, 208))
    draw.text((385, 622), "可保留", font=font(16), fill=(22, 101, 52))
    draw.text((480, 622), "轻小说语境下的内心吐槽和情绪夸张，不会被简单判死刑。", font=font(15), fill=(71, 85, 105))
    img.save(OUT / "ai-tone-detector.png")


if __name__ == "__main__":
    dashboard()
    context_builder()
    ai_tone()
    print(f"screenshots written to {OUT}")
