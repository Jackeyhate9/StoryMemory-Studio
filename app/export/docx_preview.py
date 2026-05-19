from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from docx import Document


def validate_docx_structure(path: str | Path) -> dict:
    docx_path = Path(path)
    doc = Document(docx_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return {
        "ok": docx_path.exists() and bool(paragraphs),
        "path": str(docx_path),
        "size": docx_path.stat().st_size if docx_path.exists() else 0,
        "paragraph_count": len(paragraphs),
        "first_paragraphs": paragraphs[:10],
    }


def preview_docx(path: str | Path, output_dir: str | Path = "exports/docx_preview") -> dict:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        result = validate_docx_structure(path)
        result.update(
            {
                "render_status": "skipped_no_libreoffice",
                "install_hint": "如需页面级预览，请安装 LibreOffice，并确保 soffice 可在 PATH 中访问。",
            }
        )
        return result
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(path)], check=True)
    pdf = out / (Path(path).stem + ".pdf")
    return {"render_status": "ok", "pdf_path": str(pdf), **validate_docx_structure(path)}
