"""File processing for TXT, MD, and PDF documents.

This module provides file ingestion capabilities for Memora,
extracting text content and metadata from various document formats.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from memora.core.ingestion import extract_facts
from memora.shared.models import Fact


class FileProcessor:
    """Process various file formats and extract facts."""

    def __init__(self):
        """Initialize file processor with optional dependencies."""
        self._pdf_available = False
        try:
            import PyPDF2

            self._pdf_available = True
        except ImportError:
            pass

    def process_file(self, file_path: str, source_prefix: str = "file") -> List[Fact]:
        """Process a file and extract facts.

        Args:
            file_path: Path to the file to process
            source_prefix: Prefix for source attribution (default: "file")

        Returns:
            List of extracted Fact objects

        Raises:
            ValueError: If file type is unsupported
            FileNotFoundError: If file does not exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type and process accordingly
        suffix = path.suffix.lower()

        if suffix == ".txt":
            text = self._process_text_file(path)
        elif suffix == ".md":
            text = self._process_markdown_file(path)
        elif suffix == ".pdf":
            text = self._process_pdf_file(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        # Extract facts using existing pipeline
        source = f"{source_prefix}:{path.name}"
        return extract_facts(text, source=source)

    def _process_text_file(self, path: Path) -> str:
        """Process plain text file with encoding detection.

        Args:
            path: Path to text file

        Returns:
            Decoded text content
        """
        # Try to detect encoding
        try:
            import chardet

            with open(path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)  # type: ignore[assignment]
                encoding = result["encoding"] or "utf-8"
        except ImportError:
            # Fallback to utf-8 if chardet not available
            encoding = "utf-8"

        # Read with detected encoding
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    def _process_markdown_file(self, path: Path) -> str:
        """Process Markdown file with metadata extraction.

        Args:
            path: Path to markdown file

        Returns:
            Text content with metadata preserved
        """
        # Read raw markdown content
        text = self._process_text_file(path)

        # Try to parse metadata if markdown library is available
        try:
            import markdown

            md = markdown.Markdown(extensions=["meta"])
            html = md.convert(text)

            # Extract metadata if present
            metadata = getattr(md, "Meta", {})

            # Prepend metadata as structured text
            if metadata:
                metadata_text = "\n".join(
                    [f"{key}: {' '.join(values)}" for key, values in metadata.items()]
                )
                text = f"{metadata_text}\n\n{text}"
        except ImportError:
            # If markdown library not available, just return raw text
            pass

        return text

    def _process_pdf_file(self, path: Path) -> str:
        """Process PDF file and extract text content.

        Args:
            path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            ValueError: If PDF processing is not available
        """
        if not self._pdf_available:
            raise ValueError("PDF processing not available. Install PyPDF2: pip install pypdf2")

        import PyPDF2

        text_content = []

        try:
            with open(path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")

        except Exception as e:
            raise ValueError(f"Error processing PDF: {e}")

        return "\n\n".join(text_content)

    def process_directory(
        self, directory_path: str, file_types: Optional[List[str]] = None, recursive: bool = False
    ) -> Dict[str, List[Fact]]:
        """Process all supported files in a directory.

        Args:
            directory_path: Path to directory
            file_types: List of file extensions to process (default: ['txt', 'md', 'pdf'])
            recursive: Whether to process subdirectories recursively

        Returns:
            Dictionary mapping file paths to extracted facts
        """
        if file_types is None:
            file_types = ["txt", "md", "pdf"]

        # Normalize extensions
        extensions = [f'.{ext.lower().strip(".")}' for ext in file_types]

        directory = Path(directory_path)
        results = {}

        # Find all matching files
        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                try:
                    facts = self.process_file(str(file_path))
                    results[str(file_path)] = facts
                except Exception as e:
                    # Log error but continue processing other files
                    results[str(file_path)] = []
                    print(f"Error processing {file_path}: {e}")

        return results

    def extract_file_metadata(self, file_path: str) -> Dict[str, any]:
        """Extract metadata from a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = path.stat()

        return {
            "file_name": path.name,
            "file_path": str(path.absolute()),
            "file_type": path.suffix.lower(),
            "file_size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        }
