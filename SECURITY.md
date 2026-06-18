# Security Policy

StoryMemory Studio is local-first software. It stores projects, chapters, memory databases, exports, and settings on the user's machine by default.

## Supported Version

| Version | Supported |
| --- | --- |
| v1.x | Yes |

## Reporting a Vulnerability

Please open a private security advisory on GitHub if possible, or contact the maintainer through the repository contact channels.

Do not publicly post:

- API keys;
- user manuscripts;
- `.env` files;
- SQLite databases;
- private sample chapters.

## Data Safety Notes

- `.env` may contain API keys and must not be committed.
- `data/` may contain local story databases.
- `exports/` may contain generated manuscripts.
- Cloud model providers receive context only when the user actively invokes them.
- Ollama runs through the local Ollama endpoint.

## For Users

If you share bug reports, please remove private text, names, API keys, and manuscript excerpts that you do not want public.
