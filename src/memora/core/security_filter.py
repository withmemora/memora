"""Sensitive content filtering for Memora.

Filters API keys, passwords, tokens, and PII before storage.
Critical security component - prevents accidental storage of secrets.
"""

import re
from typing import Tuple, List


class SensitiveContentFilter:
    """Detects and filters sensitive content before storage."""

    def __init__(self):
        # Regex patterns for common sensitive content
        self.patterns = [
            # API Keys & Tokens
            (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
            (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
            (r"ghu_[a-zA-Z0-9]{36}", "GitHub User-to-Server Token"),
            (r"ghs_[a-zA-Z0-9]{36}", "GitHub Server-to-Server Token"),
            (r"Bearer [a-zA-Z0-9\-\._~\+\/]+=*", "Bearer Token"),
            (r"aws_access_key_id\s*=\s*[A-Z0-9]{20}", "AWS Access Key"),
            (r"aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}", "AWS Secret Key"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
            # Database URLs
            (r"postgresql://[^@]+@[^/]+/\w+", "PostgreSQL Connection String"),
            (r"mysql://[^@]+@[^/]+/\w+", "MySQL Connection String"),
            (r"mongodb://[^@]+@[^/]+/\w+", "MongoDB Connection String"),
            (r"redis://[^@]+@[^:]+(:\d+)?", "Redis Connection String"),
            # Common password patterns
            (r'password\s*[:=]\s*["\']?[^\s"\']{8,}["\']?', "Password Assignment"),
            (r'passwd\s*[:=]\s*["\']?[^\s"\']{8,}["\']?', "Password Assignment"),
            (r'pwd\s*[:=]\s*["\']?[^\s"\']{8,}["\']?', "Password Assignment"),
            # SSH Keys
            (r"-----BEGIN [A-Z ]+PRIVATE KEY-----", "SSH Private Key"),
            (r"ssh-rsa [A-Za-z0-9+/=]+", "SSH Public Key"),
            (r"ssh-ed25519 [A-Za-z0-9+/=]+", "SSH Ed25519 Key"),
            # Email addresses (PII)
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Email Address"),
            # Credit card numbers (basic pattern)
            (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "Credit Card Number"),
            # Phone numbers (US format)
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "Phone Number"),
            (r"\(\d{3}\)\s*\d{3}[-.]?\d{4}", "Phone Number"),
            # Social Security Numbers
            (r"\b\d{3}-\d{2}-\d{4}\b", "Social Security Number"),
            # JWT Tokens
            (r"eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+", "JWT Token"),
        ]

    def scan_content(self, text: str) -> tuple[bool, list[str]]:
        """Scan text for sensitive content.

        Returns:
            (has_sensitive_content, list_of_detected_types)
        """
        if not text or not isinstance(text, str):
            return False, []

        detected = []
        for pattern, content_type in self.patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                detected.append(content_type)

        return len(detected) > 0, detected

    def filter_content(self, text: str, replacement: str = "[REDACTED]") -> tuple[str, list[str]]:
        """Filter out sensitive content from text.

        Returns:
            (filtered_text, list_of_redacted_types)
        """
        if not text or not isinstance(text, str):
            return text, []

        filtered_text = text
        redacted_types = []

        for pattern, content_type in self.patterns:
            if re.search(pattern, filtered_text, re.IGNORECASE | re.MULTILINE):
                filtered_text = re.sub(
                    pattern, replacement, filtered_text, flags=re.IGNORECASE | re.MULTILINE
                )
                redacted_types.append(content_type)

        return filtered_text, redacted_types

    def is_safe_for_storage(self, text: str) -> bool:
        """Quick check if content is safe for storage."""
        has_sensitive, _ = self.scan_content(text)
        return not has_sensitive


# Global filter instance
_global_filter = SensitiveContentFilter()


def scan_for_sensitive_content(text: str) -> tuple[bool, list[str]]:
    """Global function to scan content."""
    return _global_filter.scan_content(text)


def filter_sensitive_content(text: str, replacement: str = "[REDACTED]") -> tuple[str, list[str]]:
    """Global function to filter content."""
    return _global_filter.filter_content(text, replacement)


def is_content_safe(text: str) -> bool:
    """Global function to check safety."""
    return _global_filter.is_safe_for_storage(text)
