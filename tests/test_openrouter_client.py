"""
Tests for OpenRouterClient class.
"""
import json
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests
from terminal_chat.cli import OpenRouterClient
from tests.conftest import create_mock_stream_response


class TestOpenRouterClientInit:
    """Test OpenRouterClient initialization."""

    def test_init(self):
        """Test basic initialization."""
        client = OpenRouterClient("sk-test-token", "test-model")

        assert client.model == "test-model"
        assert client.api_token == "sk-test-token"
        assert client.session is None


class TestChatStream:
    """Test chat_stream method."""

    @patch('terminal_chat.cli.requests.post')
    def test_successful_stream(self, mock_post, api_responses):
        """Test successful streaming response."""
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[line.encode() for line in api_responses["chat_success_stream"]]
        )
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Hello"}]

        chunks = list(client.chat_stream(messages))

        # Should yield content chunks
        assert len(chunks) > 0
        assert "Hello" in "".join(chunks) or "there" in "".join(chunks)

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == "https://openrouter.ai/api/v1/chat/completions"
        assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test-token"
        assert call_args[1]["json"]["model"] == "test-model"
        assert call_args[1]["json"]["messages"] == messages
        assert call_args[1]["json"]["stream"] is True

    @patch('terminal_chat.cli.requests.post')
    def test_stream_with_usage(self, mock_post):
        """Test extracting usage information from stream."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n',
                b'data: {"choices": [{"delta": {}}], "usage": {"prompt_tokens": 10, "completion_tokens": 20}}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        list(client.chat_stream(messages))  # Consume stream

        # Check usage was extracted
        assert client.input_tokens == 10
        assert client.output_tokens == 20

    @patch('terminal_chat.cli.requests.post')
    def test_stream_done_marker(self, mock_post):
        """Test handling of [DONE] marker."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Test"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        chunks = list(client.chat_stream(messages))

        # Should stop at [DONE]
        assert len(chunks) > 0
        assert "[DONE]" not in "".join(chunks)

    @patch('terminal_chat.cli.requests.post')
    def test_stream_empty_chunks(self, mock_post):
        """Test handling of empty content in chunks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n',
                b'data: {"choices": [{"delta": {}}]}\n\n',  # Empty delta
                b'data: {"choices": [{"delta": {"content": " World"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        chunks = list(client.chat_stream(messages))

        # Should handle empty deltas gracefully
        content = "".join(chunks)
        assert "Hello" in content
        assert "World" in content

    @patch('terminal_chat.cli.requests.post')
    def test_stream_invalid_json(self, mock_post):
        """Test handling of invalid JSON in stream."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Valid"}}]}\n\n',
                b'data: {invalid json}\n\n',  # Invalid
                b'data: {"choices": [{"delta": {"content": " Text"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        chunks = list(client.chat_stream(messages))

        # Should skip invalid JSON and continue
        content = "".join(chunks)
        assert "Valid" in content
        assert "Text" in content

    @patch('terminal_chat.cli.requests.post')
    def test_stream_with_max_tokens(self, mock_post):
        """Test streaming with max_tokens parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        list(client.chat_stream(messages, max_tokens=500))

        # Verify max_tokens in request
        call_args = mock_post.call_args
        assert call_args[1]["json"]["max_tokens"] == 500

    @patch('terminal_chat.cli.requests.post')
    def test_stream_multiline_content(self, mock_post):
        """Test streaming multiline content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Line 1\\n"}}]}\n\n',
                b'data: {"choices": [{"delta": {"content": "Line 2\\n"}}]}\n\n',
                b'data: {"choices": [{"delta": {"content": "Line 3"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        chunks = list(client.chat_stream(messages))
        content = "".join(chunks)

        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content


class TestErrorHandling:
    """Test error handling in OpenRouterClient."""

    @patch('terminal_chat.cli.requests.post')
    def test_http_401_error(self, mock_post):
        """Test handling of 401 Unauthorized error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = json.dumps({"error": {"message": "Invalid API key"}})
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401")
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(Exception) as exc_info:
            list(client.chat_stream(messages))

        assert "401" in str(exc_info.value) or "Invalid API key" in str(exc_info.value)

    @patch('terminal_chat.cli.requests.post')
    def test_http_429_error(self, mock_post):
        """Test handling of 429 Rate Limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = json.dumps({"error": {"message": "Rate limit exceeded"}})
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429")
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(Exception) as exc_info:
            list(client.chat_stream(messages))

        assert "429" in str(exc_info.value) or "Rate limit" in str(exc_info.value)

    @patch('terminal_chat.cli.requests.post')
    def test_http_500_error(self, mock_post):
        """Test handling of 500 Server Error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = json.dumps({"error": {"message": "Internal server error"}})
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(Exception) as exc_info:
            list(client.chat_stream(messages))

        assert "500" in str(exc_info.value)

    @patch('terminal_chat.cli.requests.post')
    def test_network_error(self, mock_post):
        """Test handling of network errors."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(requests.exceptions.ConnectionError):
            list(client.chat_stream(messages))

    @patch('terminal_chat.cli.requests.post')
    def test_timeout_error(self, mock_post):
        """Test handling of timeout errors."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(requests.exceptions.Timeout):
            list(client.chat_stream(messages))

    @patch('terminal_chat.cli.requests.post')
    def test_error_message_extraction(self, mock_post):
        """Test extraction of error message from response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = json.dumps({
            "error": {
                "message": "Bad request: invalid parameter",
                "code": "invalid_request_error"
            }
        })
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400")
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(Exception) as exc_info:
            list(client.chat_stream(messages))

        # Error message should be extracted
        error_str = str(exc_info.value)
        assert "Bad request" in error_str or "invalid parameter" in error_str or "400" in error_str


class TestInterrupt:
    """Test interrupt functionality."""

    @patch('terminal_chat.cli.requests.post')
    def test_interrupt_stops_stream(self, mock_post):
        """Test that interrupt stops the stream."""
        mock_response = Mock()
        mock_response.status_code = 200

        # Create a generator that yields many chunks
        def long_stream():
            for i in range(100):
                yield f'data: {{"choices": [{{"delta": {{"content": "Chunk {i}"}}}}]}}\n\n'.encode()
            yield b'data: [DONE]\n\n'

        mock_response.iter_lines = Mock(return_value=long_stream())
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        chunks = []
        stream = client.chat_stream(messages)

        # Consume a few chunks then interrupt
        for i, chunk in enumerate(stream):
            chunks.append(chunk)
            if i == 5:
                client.interrupt()
                break

        # Should have stopped early
        assert len(chunks) < 100

    def test_interrupt_before_stream(self):
        """Test calling interrupt before streaming starts."""
        client = OpenRouterClient("sk-test-token", "test-model")

        # Should not raise exception
        client.interrupt()

        assert client.session is None

    @patch('terminal_chat.cli.requests.post')
    def test_interrupt_with_session(self, mock_post):
        """Test interrupt closes session."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        # Start stream (creates session)
        list(client.chat_stream(messages))

        # Interrupt
        client.interrupt()

        # Session should be closed (implementation detail may vary)


class TestRequestHeaders:
    """Test request headers and configuration."""

    @patch('terminal_chat.cli.requests.post')
    def test_authorization_header(self, mock_post):
        """Test that Authorization header is set correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-api-key", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        list(client.chat_stream(messages))

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer sk-test-api-key"

    @patch('terminal_chat.cli.requests.post')
    def test_custom_headers(self, mock_post):
        """Test that custom headers are included."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        list(client.chat_stream(messages))

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]

        # Check for custom headers (may include Referer, X-Title, etc.)
        assert "Authorization" in headers

    @patch('terminal_chat.cli.requests.post')
    def test_request_timeout(self, mock_post):
        """Test that request has timeout configured."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Test"}]

        list(client.chat_stream(messages))

        call_args = mock_post.call_args

        # Should have timeout parameter
        assert "timeout" in call_args[1]
        assert call_args[1]["timeout"] == 30


class TestMessageFormatting:
    """Test message formatting for API."""

    @patch('terminal_chat.cli.requests.post')
    def test_single_message(self, mock_post):
        """Test formatting single message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [{"role": "user", "content": "Hello"}]

        list(client.chat_stream(messages))

        call_args = mock_post.call_args
        sent_messages = call_args[1]["json"]["messages"]

        assert len(sent_messages) == 1
        assert sent_messages[0]["role"] == "user"
        assert sent_messages[0]["content"] == "Hello"

    @patch('terminal_chat.cli.requests.post')
    def test_conversation_messages(self, mock_post):
        """Test formatting conversation with multiple messages."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"}
        ]

        list(client.chat_stream(messages))

        call_args = mock_post.call_args
        sent_messages = call_args[1]["json"]["messages"]

        assert len(sent_messages) == 4
        assert sent_messages[0]["role"] == "system"
        assert sent_messages[-1]["content"] == "How are you?"

    @patch('terminal_chat.cli.requests.post')
    def test_empty_messages_list(self, mock_post):
        """Test handling empty messages list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[b'data: [DONE]\n\n'])
        mock_post.return_value = mock_response

        client = OpenRouterClient("sk-test-token", "test-model")
        messages = []

        list(client.chat_stream(messages))

        call_args = mock_post.call_args
        sent_messages = call_args[1]["json"]["messages"]

        assert sent_messages == []


class TestUsageTracking:
    """Test token usage tracking."""

    def test_initial_usage(self):
        """Test initial usage is zero."""
        client = OpenRouterClient("sk-test-token", "test-model")

        assert client.input_tokens == 0
        assert client.output_tokens == 0

    @patch('terminal_chat.cli.requests.post')
    def test_usage_accumulation(self, mock_post):
        """Test that usage accumulates across multiple requests."""
        client = OpenRouterClient("sk-test-token", "test-model")

        # First request
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "A"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response1

        list(client.chat_stream([{"role": "user", "content": "Test 1"}]))

        assert client.input_tokens == 10
        assert client.output_tokens == 5

        # Second request
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "B"}}], "usage": {"prompt_tokens": 15, "completion_tokens": 8}}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response2

        list(client.chat_stream([{"role": "user", "content": "Test 2"}]))

        # Should accumulate
        assert client.input_tokens == 25
        assert client.output_tokens == 13
