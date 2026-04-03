"""Code memory extractor.

Extracts code-related memories from code blocks and code patterns.
"""

from __future__ import annotations

import re

from memora.shared.models import Memory, MemorySource, MemoryType, now_iso


def extract_code_memories(
    text: str,
    source: str = "ollama_chat",
    session_id: str = "",
    branch: str = "main",
    turn_index: int = 0,
) -> list[Memory]:
    """Extract memories from code in text."""
    memories: list[Memory] = []

    code_blocks = _extract_code_blocks(text)
    for lang, code in code_blocks:
        summary = _summarize_code(code, lang)
        func_names = _extract_function_names(code, lang)
        class_names = _extract_class_names(code, lang)

        mem = Memory(
            id=Memory.generate_id(),
            content=summary,
            memory_type=MemoryType.CODE,
            confidence=0.90,
            source=MemorySource.OLLAMA_CHAT,
            session_id=session_id,
            branch=branch,
            turn_index=turn_index,
            created_at=now_iso(),
            updated_at=now_iso(),
            metadata={
                "language": lang,
                "raw_code": code,
                "summary": summary,
                "function_names": func_names,
                "class_names": class_names,
            },
        )
        memories.append(mem)

    return memories


def _extract_code_blocks(text: str) -> list[tuple[str, str]]:
    pattern = r"```(\w*)\s*\n?(.*?)```"
    blocks = re.findall(pattern, text, re.DOTALL)
    results = []
    for lang, code in blocks:
        if code.strip():
            lang = lang.lower() if lang else "unknown"
            results.append((lang, code.strip()))
    return results


def _summarize_code(code: str, lang: str) -> str:
    lines = code.strip().split("\n")
    first_line = lines[0].strip() if lines else ""

    func_match = re.match(r"def\s+(\w+)", first_line)
    if func_match:
        return f"{lang.capitalize()} function: {func_match.group(1)}"

    class_match = re.match(r"class\s+(\w+)", first_line)
    if class_match:
        return f"{lang.capitalize()} class: {class_match.group(1)}"

    func_js = re.match(r"(?:function\s+(\w+)|const\s+(\w+)\s*=)", first_line)
    if func_js:
        name = func_js.group(1) or func_js.group(2)
        return f"JavaScript function: {name}"

    return f"{lang.capitalize()} code snippet ({len(lines)} lines)"


def _extract_function_names(code: str, lang: str) -> list[str]:
    names: list[str] = []
    if lang in ("python", "py"):
        names.extend(re.findall(r"def\s+(\w+)\s*\(", code))
    elif lang in ("javascript", "typescript", "js", "ts"):
        names.extend(re.findall(r"function\s+(\w+)\s*\(", code))
        names.extend(re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(", code))
    return names


def _extract_class_names(code: str, lang: str) -> list[str]:
    if lang in ("python", "py"):
        return re.findall(r"class\s+(\w+)", code)
    elif lang in ("javascript", "typescript", "js", "ts"):
        return re.findall(r"class\s+(\w+)", code)
    return []
