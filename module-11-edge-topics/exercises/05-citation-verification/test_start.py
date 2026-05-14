"""Tests for Exercise 05 — Citation Verification."""

from unittest.mock import MagicMock, call
from start import extract_claims, check_claim_support, verify_answer


def make_mock_client(response_text):
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = response_text
    client.chat.completions.create.return_value = response
    return client


class TestExtractClaims:
    def test_returns_list_of_strings(self):
        client = make_mock_client("The reactor is hot.\nThe hull is intact.")
        claims = extract_claims(client, "The reactor is hot and the hull is intact.")
        assert isinstance(claims, list)
        assert all(isinstance(c, str) for c in claims)

    def test_extracts_multiple_claims(self):
        client = make_mock_client("Claim one.\nClaim two.\nClaim three.")
        claims = extract_claims(client, "Some answer with three claims.")
        assert len(claims) == 3

    def test_filters_empty_lines(self):
        client = make_mock_client("Claim one.\n\n\nClaim two.\n")
        claims = extract_claims(client, "Answer text.")
        assert len(claims) == 2
        assert all(len(c) > 0 for c in claims)

    def test_calls_openai(self):
        client = make_mock_client("A single claim.")
        extract_claims(client, "Answer text.")
        client.chat.completions.create.assert_called_once()


class TestCheckClaimSupport:
    def test_returns_supported(self):
        client = make_mock_client("supported")
        result = check_claim_support(client, "The reactor is hot.", "Reactor temperature: 5000K")
        assert result == "supported"

    def test_returns_unsupported(self):
        client = make_mock_client("unsupported")
        result = check_claim_support(client, "The crew is large.", "The ship has 5 decks.")
        assert result == "unsupported"

    def test_returns_string(self):
        client = make_mock_client("supported")
        result = check_claim_support(client, "claim", "passage")
        assert isinstance(result, str)
        assert result in ("supported", "unsupported")


class TestVerifyAnswer:
    def test_returns_list_of_dicts(self):
        responses = iter(["Claim A.\nClaim B.", "supported", "unsupported"])
        client = MagicMock()

        def create_response(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = next(responses)
            return resp

        client.chat.completions.create.side_effect = create_response

        results = verify_answer(client, "Answer text.", ["Passage 1"])
        assert isinstance(results, list)
        for r in results:
            assert "claim" in r
            assert "supported" in r
            assert isinstance(r["supported"], bool)

    def test_marks_supported_claims(self):
        responses = iter(["Single claim.", "supported"])
        client = MagicMock()

        def create_response(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = next(responses)
            return resp

        client.chat.completions.create.side_effect = create_response

        results = verify_answer(client, "Answer.", ["Evidence passage"])
        assert results[0]["supported"] is True
        assert results[0]["supporting_passage"] == "Evidence passage"

    def test_marks_unsupported_claims(self):
        responses = iter(["Single claim.", "unsupported"])
        client = MagicMock()

        def create_response(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = next(responses)
            return resp

        client.chat.completions.create.side_effect = create_response

        results = verify_answer(client, "Answer.", ["Unrelated passage"])
        assert results[0]["supported"] is False
        assert results[0]["supporting_passage"] is None

    def test_checks_all_passages(self):
        responses = iter(["Claim X.", "unsupported", "supported"])
        client = MagicMock()

        def create_response(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = next(responses)
            return resp

        client.chat.completions.create.side_effect = create_response

        results = verify_answer(client, "Answer.", ["Passage A", "Passage B"])
        assert results[0]["supported"] is True
        assert results[0]["supporting_passage"] == "Passage B"
