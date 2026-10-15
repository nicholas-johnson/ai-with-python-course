"""Tests for Exercise 04 — Faithfulness."""

from unittest.mock import MagicMock

from start import check_support, extract_claims, score_faithfulness


def make_mock_client(response_text: str):
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = response_text
    client.chat.completions.create.return_value = response
    return client


def client_from_queue(texts: list[str]):
    queue = list(texts)

    def create(**kwargs):
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = queue.pop(0)
        return resp

    client = MagicMock()
    client.chat.completions.create.side_effect = create
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


class TestCheckSupport:
    def test_returns_supported(self):
        client = make_mock_client("supported")
        result = check_support(client, "The reactor is hot.", "Reactor temperature: 5000K")
        assert result == "supported"

    def test_returns_unsupported(self):
        client = make_mock_client("unsupported")
        assert check_support(client, "The crew is large.", "The ship has 5 decks.") == "unsupported"

    def test_only_two_labels(self):
        client = make_mock_client("supported")
        result = check_support(client, "claim", "context")
        assert result in ("supported", "unsupported")


class TestScoreFaithfulness:
    def test_ratio_all_supported(self):
        client = client_from_queue(["Claim A.\nClaim B.", "supported", "supported"])
        result = score_faithfulness(client, "Answer.", "Context.")
        assert result["num_claims"] == 2
        assert result["num_supported"] == 2
        assert result["faithfulness"] == 1.0
        assert result["claims"][0]["supported"] is True

    def test_ratio_half(self):
        client = client_from_queue(["Claim A.\nClaim B.", "supported", "unsupported"])
        result = score_faithfulness(client, "Answer.", "Context.")
        assert result["faithfulness"] == 0.5
        assert result["num_supported"] == 1

    def test_zero_claims_is_faithful(self):
        client = client_from_queue([""])
        result = score_faithfulness(client, "", "Context.")
        assert result["num_claims"] == 0
        assert result["faithfulness"] == 1.0

    def test_keeps_claim_text(self):
        client = client_from_queue(["Warp core at 94%.", "supported"])
        result = score_faithfulness(client, "Warp core at 94%.", "Warp core operating at 94%.")
        assert result["claims"][0]["claim"] == "Warp core at 94%."
