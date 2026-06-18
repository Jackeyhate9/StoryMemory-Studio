# Contributing to StoryMemory Studio

Thanks for considering a contribution.

StoryMemory Studio welcomes bug reports, workflow notes, model compatibility reports, prompt improvements, UI fixes, and documentation.

欢迎提交 bug、模型适配报告、长篇连贯性案例、Prompt 改进、UI 优化和文档修订。

## Good First Contributions

- Fix Chinese/English documentation.
- Add screenshots or short demo notes.
- Report model behavior for DeepSeek, GLM-5.2, Ollama, and OpenAI-compatible gateways.
- Improve Streamlit UI copy.
- Add tests for output cleaning, JSON repair, memory extraction, or exports.

## Development Setup

```powershell
git clone https://github.com/Jackeyhate9/StoryMemory-Studio.git
cd StoryMemory-Studio
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli init
python run_ui.py
```

## Tests

```powershell
python -m pytest -q
python -m compileall app tests -q
```

## Contribution Rules

- Do not commit `.env`, local databases, generated novels, or private user data.
- Keep user data local-first.
- Do not add prompts that encourage copying protected text.
- Keep model-specific behavior behind provider settings.
- Prefer small, focused pull requests.

## Reporting Model Issues

When reporting model output issues, include:

- provider and model name;
- prompt mode or UI page;
- whether `<think>` / English draft / repeated text appeared;
- whether output was generated through StoryMemory Studio or raw chat;
- a short, sanitized excerpt.

Please avoid posting private manuscripts or full copyrighted samples.
