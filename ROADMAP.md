# StoryMemory Studio Roadmap

StoryMemory Studio is currently a Windows-first MVP for long-form fiction memory and AI-assisted chapter creation.

StoryMemory Studio 当前是面向 Windows 普通用户的 MVP：本地优先、结构化记忆、长上下文编排、章节生成、一致性检查和 IP 改编。

## v1.0.x Stabilization

- Improve Windows exe startup reliability and antivirus false-positive notes.
- Add more model connection presets for DeepSeek, GLM-5.2, OpenAI-compatible gateways, and Ollama.
- Strengthen output cleaning for reasoning traces, English planning text, and repeated text.
- Improve docx export templates and one-click project backup.
- Add more real-world smoke tests for long chapter chains.

## v1.1 Memory Authoring

- Richer visual memory editor for characters, relationships, foreshadows, timeline events, and world rules.
- Memory diff view before committing extracted facts.
- Safer merge workflow for imported existing novels.
- Better volume-level and arc-level outline management.

## v1.2 Long-Context Evaluation

- DeepSeek long-context audit mode for whole-volume consistency.
- Recall evaluation reports: which hard facts were included, omitted, or contradicted.
- More explicit token-budget visualization for `lite`, `standard`, `deepseek_long`, and `full_audit`.
- Benchmark examples for long-form story continuity.

## v1.3 Style and Novelization

- More controllable `humanizer-zh` and Novelization Rewriter settings.
- Style profile comparison and export.
- Safer style-transfer guardrails to avoid copying sample text.
- Dialogue subtext and scene-friction suggestions.

## v1.4 IP Adaptation

- Better comic storyboard exports.
- Short drama script templates.
- AI video storyboard prompt packs.
- Xiaohongshu / teaser / poster copy workflow.

## v2.0 Collaboration and Web

- Optional FastAPI backend.
- Multi-project dashboard.
- Plugin-style model providers.
- Optional cloud sync while keeping local-first storage as the default.

## Community Ideas

If you use StoryMemory Studio for web novels, short dramas, comics, or worldbuilding, please open a GitHub Discussion with:

- your workflow;
- model used;
- chapter length;
- memory problems found;
- what improved or failed.

中文用户也欢迎直接在 Discussions 里提交：模型测试、长篇连贯性问题、AI 腔案例、导入已有作品流程、Windows exe 反馈。
