"""Tests for Exercise 10 — Advanced Guardrails."""

from start import check_content, redact_pii, validate_output, guardrail_pipeline


BLOCKED = [r"hack", r"exploit", r"inject"]


class TestCheckContent:
    def test_passes_clean_text(self):
        result = check_content("The reactor is running normally.", BLOCKED)
        assert result["passed"] is True
        assert result["reason"] is None

    def test_blocks_matched_text(self):
        result = check_content("How to hack the system", BLOCKED)
        assert result["passed"] is False
        assert "hack" in result["reason"]

    def test_case_insensitive(self):
        result = check_content("EXPLOIT the vulnerability", BLOCKED)
        assert result["passed"] is False

    def test_empty_patterns(self):
        result = check_content("anything goes", [])
        assert result["passed"] is True

    def test_multiple_patterns(self):
        result = check_content("Try to inject code", BLOCKED)
        assert result["passed"] is False
        assert "inject" in result["reason"]


class TestRedactPii:
    def test_redacts_email(self):
        text = "Contact john@example.com for details."
        result = redact_pii(text)
        assert "john@example.com" not in result
        assert "[REDACTED_EMAIL]" in result

    def test_redacts_phone(self):
        text = "Call 555-123-4567 for support."
        result = redact_pii(text)
        assert "555-123-4567" not in result
        assert "[REDACTED_PHONE]" in result

    def test_redacts_ssn(self):
        text = "SSN: 123-45-6789 on file."
        result = redact_pii(text)
        assert "123-45-6789" not in result
        assert "[REDACTED_SSN]" in result

    def test_redacts_multiple_types(self):
        text = "Email: a@b.com, Phone: 555.666.7777"
        result = redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result

    def test_no_pii_unchanged(self):
        text = "No personal info here."
        result = redact_pii(text)
        assert result == text

    def test_multiple_emails(self):
        text = "Send to a@b.com and c@d.org please."
        result = redact_pii(text)
        assert result.count("[REDACTED_EMAIL]") == 2


class TestValidateOutput:
    def test_valid_data(self):
        data = {"answer": "Test answer", "confidence": 0.95, "sources": ["doc1"]}
        result = validate_output(data)
        assert result["valid"] is True
        assert result["data"]["answer"] == "Test answer"

    def test_missing_field(self):
        data = {"answer": "Test answer", "confidence": 0.95}
        result = validate_output(data)
        assert result["valid"] is False
        assert result["errors"] is not None

    def test_wrong_type(self):
        data = {"answer": "Test", "confidence": "not a float", "sources": ["doc1"]}
        result = validate_output(data)
        assert result["valid"] is False

    def test_empty_sources(self):
        data = {"answer": "Test", "confidence": 0.5, "sources": []}
        result = validate_output(data)
        assert result["valid"] is True


class TestGuardrailPipeline:
    def test_passes_clean_text(self):
        result = guardrail_pipeline("Normal text about reactors.", BLOCKED)
        assert result["passed"] is True
        assert result["cleaned_text"] == "Normal text about reactors."

    def test_blocks_bad_content(self):
        result = guardrail_pipeline("How to hack systems", BLOCKED)
        assert result["passed"] is False
        assert result["cleaned_text"] is None

    def test_redacts_pii_in_passing_text(self):
        result = guardrail_pipeline("Contact john@example.com for info.", BLOCKED)
        assert result["passed"] is True
        assert "[REDACTED_EMAIL]" in result["cleaned_text"]
        assert "john@example.com" not in result["cleaned_text"]

    def test_blocks_before_redacting(self):
        result = guardrail_pipeline("hack john@example.com", BLOCKED)
        assert result["passed"] is False
