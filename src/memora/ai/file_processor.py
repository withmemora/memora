"""File processing for TXT, MD, and PDF documents.

v3.0: Outputs Memory objects via the new extraction pipeline.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from memora.core.ingestion import extract_memories
from memora.shared.models import Memory


class FileProcessor:
    """Process various file formats and extract memories."""

    def __init__(self):
        self._pdf_available = False
        try:
            import pypdf

            self._pdf_available = True
        except ImportError:
            pass

    def process_file(self, file_path: str, source_prefix: str = "file") -> List[Memory]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix == ".txt":
            text = self._process_text_file(path)
        elif suffix == ".md":
            text = self._process_markdown_file(path)
        elif suffix == ".pdf":
            text = self._process_pdf_file(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        file_type = suffix.lstrip(".")
        memories, _, _ = extract_memories(
            text,
            source=f"{source_prefix}:{path.name}",
            filename=path.name,
            file_type=file_type,
        )
        return memories

    def _process_text_file(self, path: Path) -> str:
        try:
            import chardet

            with open(path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result["encoding"] or "utf-8"
        except ImportError:
            encoding = "utf-8"

        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    def _process_markdown_file(self, path: Path) -> str:
        text = self._process_text_file(path)
        try:
            import markdown

            md = markdown.Markdown(extensions=["meta"])
            html = md.convert(text)
            metadata = getattr(md, "Meta", {})
            if metadata:
                metadata_text = "\n".join(
                    [f"{key}: {' '.join(values)}" for key, values in metadata.items()]
                )
                text = f"{metadata_text}\n\n{text}"
        except ImportError:
            pass
        return text

    def _process_pdf_file(self, path: Path) -> str:
        if not self._pdf_available:
            raise ValueError("PDF processing not available. Install pypdf: pip install pypdf")

        import pypdf

        text_content = []

        try:
            with open(path, "rb") as f:
                pdf_reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")
        except Exception as e:
            raise ValueError(f"Error processing PDF: {e}")

        return "\n\n".join(text_content)

    def process_directory(
        self, directory_path: str, file_types: Optional[List[str]] = None, recursive: bool = False
    ) -> Dict[str, List[Memory]]:
        if file_types is None:
            file_types = ["txt", "md", "pdf"]

        extensions = [f'.{ext.lower().strip(".")}' for ext in file_types]
        directory = Path(directory_path)
        results = {}

        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                try:
                    memories = self.process_file(str(file_path))
                    results[str(file_path)] = memories
                except Exception as e:
                    results[str(file_path)] = []
                    print(f"Error processing {file_path}: {e}")

        return results
