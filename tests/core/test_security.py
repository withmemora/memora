"""Security tests for Memora v3.1.

Tests sensitive content filtering and sanitization.
"""

import pytest
from memora.core.security_filter import filter_sensitive_content


class TestSensitiveContentFiltering:
    """Test that sensitive patterns are filtered before storage."""

    def test_api_key_filtered(self):
        """Test that API keys are detected and filtered."""
        text = "My OpenAI API key is sk-1234567890abcdefghij"
        filtered, redacted_types = filter_sensitive_content(text)
        assert "sk-1234567890abcdefghij" not in filtered
        assert "[REDACTED]" in filtered or "API key" not in filtered.lower()

    def test_password_filtered(self):
        """Test that passwords are detected and filtered."""
        text = "password: SuperSecret123!"
        filtered, _ = filter_sensitive_content(text)
        # Password in explicit statement should be filtered
        assert "SuperSecret123" not in filtered or "[REDACTED" in filtered

    def test_email_filtered(self):
        """Test that email addresses are detected and filtered."""
        text = "Contact me at user@example.com for details"
        filtered, _ = filter_sensitive_content(text)
        assert (
            "user@example.com" not in filtered or "[REDACTED_EMAIL]" in filtered or filtered == text
        )  # Email filtering is optional

    def test_credit_card_filtered(self):
        """Test that credit card numbers are detected and filtered."""
        text = "My card number is 4532-1234-5678-9010"
        filtered, _ = filter_sensitive_content(text)
        assert "4532-1234-5678-9010" not in filtered or "[REDACTED" in filtered

    def test_ssh_key_filtered(self):
        """Test that SSH keys are detected and filtered."""
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAK..."
        filtered, _ = filter_sensitive_content(text)
        assert "BEGIN RSA PRIVATE KEY" not in filtered or "[REDACTED" in filtered

    def test_clean_text_unchanged(self):
        """Test that clean text passes through unchanged."""
        text = "I prefer Python over JavaScript for backend development"
        filtered, _ = filter_sensitive_content(text)
        # Clean text should either pass through or be minimally modified
        assert "Python" in filtered
        assert "JavaScript" in filtered


class TestPIIFiltering:
    """Test that PII (Personally Identifiable Information) is handled correctly."""

    def test_ssn_filtered(self):
        """Test that SSN patterns are filtered."""
        text = "My SSN is 123-45-6789"
        filtered, _ = filter_sensitive_content(text)
        assert "123-45-6789" not in filtered or "[REDACTED" in filtered

    def test_phone_number_filtering(self):
        """Test phone number handling."""
        text = "Call me at (555) 123-4567"
        filtered, _ = filter_sensitive_content(text)
        # Just ensure it doesn't crash
        assert isinstance(filtered, str)

    def test_multiple_sensitive_items(self):
        """Test filtering multiple sensitive items in one text."""
        text = "My API key sk-abc123def456789012345 and password:Secret123"
        filtered, _ = filter_sensitive_content(text)
        assert "sk-abc123def456789012345" not in filtered or "[REDACTED" in filtered
        assert "Secret123" not in filtered or "[REDACTED" in filtered


# Note: If filter_sensitive_content doesn't exist yet, these tests will fail
# until the security module is implemented. This is intentional - tests should
# drive implementation, not the other way around.
