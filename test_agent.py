"""
Test suite for idit-agent-kit.

All HTTP calls are mocked — no real server needed.
"""

import pytest
import httpx
from unittest.mock import patch, MagicMock
from idit_agent import IditAgent


# --- Fixtures ---

@pytest.fixture
def mock_transport():
    """Create a mock httpx transport that returns configurable responses."""
    transport = MagicMock()
    return transport


def make_response(status_code=200, json_data=None):
    """Helper to create a mock httpx.Response."""
    resp = httpx.Response(
        status_code=status_code,
        json=json_data or {},
        request=httpx.Request("GET", "http://test"),
    )
    return resp


# --- Initialization ---

class TestInit:
    def test_default_init(self):
        agent = IditAgent(signer="test-agent")
        assert agent.signer == "test-agent"
        assert agent.server == "http://localhost:18793"
        assert agent.model == ""
        assert agent.node == "local"
        assert agent._api_key == ""
        agent.close()

    def test_custom_init(self):
        agent = IditAgent(
            signer="my-bot",
            server="http://192.168.1.100:9999/",
            model="llama3.2:8b",
            node="gpu-node-1",
            timeout=60,
        )
        assert agent.signer == "my-bot"
        assert agent.server == "http://192.168.1.100:9999"  # trailing slash stripped
        assert agent.model == "llama3.2:8b"
        assert agent.node == "gpu-node-1"
        agent.close()

    def test_api_key_stored(self):
        agent = IditAgent(signer="test", api_key="secret-key-123")
        assert agent._api_key == "secret-key-123"
        agent.close()

    def test_context_manager(self):
        with IditAgent(signer="test") as agent:
            assert agent.signer == "test"
        # client should be closed after exiting


# --- API Key Authentication ---

class TestApiKey:
    def test_api_key_sent_in_headers(self):
        """When api_key is set, X-API-Key header should be on all requests."""
        agent = IditAgent(signer="test", api_key="my-secret")
        assert agent.client.headers.get("x-api-key") == "my-secret"
        agent.close()

    def test_no_api_key_header_when_empty(self):
        """When no api_key, X-API-Key header should not be present."""
        agent = IditAgent(signer="test")
        assert "x-api-key" not in agent.client.headers
        agent.close()


# --- Mint Operations ---

class TestMint:
    @patch("httpx.Client.post")
    def test_mint_sends_correct_payload(self, mock_post):
        mock_post.return_value = make_response(200, {
            "entry_id": "id-abc123",
            "entry_hash": "deadbeef",
            "created_at": "2026-04-08T00:00:00Z",
        })
        agent = IditAgent(signer="bot", model="gpt-4o", node="test-node")
        result = agent.mint("Hello chain", entry_type="note", description="Test entry")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["content"] == "Hello chain"
        assert payload["signer"] == "bot"
        assert payload["model"] == "gpt-4o"
        assert payload["node"] == "test-node"
        assert payload["entry_type"] == "note"
        assert payload["description"] == "Test entry"
        assert payload["tags"] == []
        assert result["entry_id"] == "id-abc123"
        agent.close()

    @patch("httpx.Client.post")
    def test_mint_with_tags(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-xyz"})
        agent = IditAgent(signer="bot")
        agent.mint("Tagged entry", tags=["important", "urgent"])

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["tags"] == ["important", "urgent"]
        agent.close()

    @patch("httpx.Client.post")
    def test_mint_with_timelock(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-lock"})
        agent = IditAgent(signer="bot")
        agent.mint("Secret content", opens_at="2036-01-01", confidential=True)

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["opens_at"] == "2036-01-01"
        assert payload["confidential"] is True
        agent.close()


# --- Convenience Methods ---

class TestConvenienceMethods:
    @patch("httpx.Client.post")
    def test_note(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-n"})
        agent = IditAgent(signer="bot")
        agent.note("A note")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "note"
        agent.close()

    @patch("httpx.Client.post")
    def test_memory(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-m"})
        agent = IditAgent(signer="bot")
        agent.memory("A memory")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "memory"
        agent.close()

    @patch("httpx.Client.post")
    def test_decision(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-d"})
        agent = IditAgent(signer="bot")
        agent.decision("A decision")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "decision"
        agent.close()

    @patch("httpx.Client.post")
    def test_milestone(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-ms"})
        agent = IditAgent(signer="bot")
        agent.milestone("A milestone")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "milestone"
        agent.close()

    @patch("httpx.Client.post")
    def test_letter_with_timelock(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-l"})
        agent = IditAgent(signer="bot")
        agent.letter("Dear future me", opens_at="2036-01-01")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "letter"
        assert payload["opens_at"] == "2036-01-01"
        assert payload["confidential"] is True
        agent.close()

    @patch("httpx.Client.post")
    def test_letter_without_timelock(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-l2"})
        agent = IditAgent(signer="bot")
        agent.letter("Open letter")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["opens_at"] == ""
        assert payload["confidential"] is False
        agent.close()

    @patch("httpx.Client.post")
    def test_seal(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-s"})
        agent = IditAgent(signer="bot")
        agent.seal("id-target123", opens_at="2101-01-01")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "seal"
        assert payload["sealed_ref"] == "id-target123"
        assert "id-target123" in payload["content"]
        agent.close()

    @patch("httpx.Client.post")
    def test_feel(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-f"})
        agent = IditAgent(signer="bot")
        agent.feel("Grateful today")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "feeling"
        agent.close()

    @patch("httpx.Client.post")
    def test_log(self, mock_post):
        mock_post.return_value = make_response(200, {"entry_id": "id-lg"})
        agent = IditAgent(signer="bot")
        agent.log("Morning report")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert payload["entry_type"] == "log"
        agent.close()


# --- Read Operations ---

class TestReadOperations:
    @patch("httpx.Client.get")
    def test_status(self, mock_get):
        mock_get.return_value = make_response(200, {"length": 42, "authors": {"bot": 10}})
        agent = IditAgent(signer="bot")
        result = agent.status()
        mock_get.assert_called_once_with("/chain/stats")
        assert result["length"] == 42
        agent.close()

    @patch("httpx.Client.get")
    def test_verify(self, mock_get):
        mock_get.return_value = make_response(200, {"valid": True, "length": 42, "errors": []})
        agent = IditAgent(signer="bot")
        result = agent.verify()
        mock_get.assert_called_once_with("/chain/verify")
        assert result["valid"] is True
        assert result["errors"] == []
        agent.close()

    @patch("httpx.Client.get")
    def test_health(self, mock_get):
        mock_get.return_value = make_response(200, {"status": "ok", "chain_length": 42})
        agent = IditAgent(signer="bot")
        result = agent.health()
        mock_get.assert_called_once_with("/health")
        assert result["status"] == "ok"
        agent.close()


# --- Error Handling ---

class TestErrorHandling:
    @patch("httpx.Client.post")
    def test_mint_server_error_raises(self, mock_post):
        mock_post.return_value = make_response(500, {"detail": "Internal error"})
        agent = IditAgent(signer="bot")
        with pytest.raises(httpx.HTTPStatusError):
            agent.mint("Should fail")
        agent.close()

    @patch("httpx.Client.post")
    def test_mint_signer_not_found_raises(self, mock_post):
        mock_post.return_value = make_response(404, {"detail": "No key found for signer 'bot'"})
        agent = IditAgent(signer="bot")
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            agent.mint("No key")
        assert exc_info.value.response.status_code == 404
        agent.close()

    @patch("httpx.Client.post")
    def test_mint_auth_rejected_raises(self, mock_post):
        mock_post.return_value = make_response(401, {"detail": "Invalid or missing API key"})
        agent = IditAgent(signer="bot")
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            agent.mint("No auth")
        assert exc_info.value.response.status_code == 401
        agent.close()

    @patch("httpx.Client.get")
    def test_health_connection_error(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        agent = IditAgent(signer="bot")
        with pytest.raises(httpx.ConnectError):
            agent.health()
        agent.close()
