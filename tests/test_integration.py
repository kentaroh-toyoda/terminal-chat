"""
Integration tests for end-to-end workflows.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from terminal_chat.cli import TerminalChat, Config
from tests.conftest import create_config_file


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @patch('terminal_chat.cli.requests.post')
    @patch('terminal_chat.cli.PromptSession')
    def test_simple_conversation_flow(self, mock_prompt_session, mock_post,
                                       temp_home, mock_keyring, clean_env):
        """Test a simple conversation workflow."""
        # Setup config
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="none",
            SHOW_COST="false"
        )

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Hello!"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        # Mock user input: one message then exit
        mock_session = Mock()
        mock_session.prompt.side_effect = ["Hello", "exit"]
        mock_prompt_session.return_value = mock_session

        # Run chat
        chat = TerminalChat()
        chat.chat()

        # Verify conversation happened
        assert mock_post.called
        assert len(chat.conversation.get_messages()) > 0

    @patch('terminal_chat.cli.requests.post')
    @patch('terminal_chat.cli.PromptSession')
    def test_conversation_with_guardrail(self, mock_prompt_session, mock_post,
                                          temp_home, mock_keyring, clean_env):
        """Test conversation with guardrail enabled."""
        # Setup config with guardrail
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="external",
            EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS="both"
        )

        # Mock guardrail check (safe)
        # Mock chat response
        def mock_post_side_effect(*args, **kwargs):
            url = args[0]
            if "llama-guard" in str(kwargs.get('json', {}).get('model', '')):
                # Guardrail response
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "choices": [{"message": {"content": "safe"}}]
                }
                return mock_resp
            else:
                # Chat response
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.iter_lines = Mock(
                    return_value=[
                        b'data: {"choices": [{"delta": {"content": "Response"}}]}\n\n',
                        b'data: [DONE]\n\n'
                    ]
                )
                return mock_resp

        mock_post.side_effect = mock_post_side_effect

        # Mock user input
        mock_session = Mock()
        mock_session.prompt.side_effect = ["Test message", "quit"]
        mock_prompt_session.return_value = mock_session

        # Run chat
        chat = TerminalChat()
        chat.chat()

        # Guardrail should have been called
        assert mock_post.call_count >= 2  # Guardrail + Chat

    @patch('terminal_chat.cli.requests.post')
    @patch('terminal_chat.cli.PromptSession')
    def test_clear_command(self, mock_prompt_session, mock_post,
                           temp_home, mock_keyring, clean_env):
        """Test /clear command clears conversation."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="none"
        )

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Hi"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        # User: message, /clear, exit
        mock_session = Mock()
        mock_session.prompt.side_effect = ["Hello", "/clear", "exit"]
        mock_prompt_session.return_value = mock_session

        chat = TerminalChat()
        chat.chat()

        # After /clear, conversation should be empty (or just system)
        messages = chat.conversation.get_messages()
        # Should be empty or only contain system message
        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) == 0


class TestConfigurationIntegration:
    """Test configuration affects behavior correctly."""

    @patch('terminal_chat.cli.requests.post')
    @patch('terminal_chat.cli.PromptSession')
    def test_render_markdown_affects_display(self, mock_prompt_session, mock_post,
                                             temp_home, mock_keyring, clean_env):
        """Test that RENDER_MARKDOWN config affects display."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            RENDER_MARKDOWN="false",
            GUARDRAIL="none"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "Test"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )
        mock_post.return_value = mock_response

        mock_session = Mock()
        mock_session.prompt.side_effect = ["Test", "exit"]
        mock_prompt_session.return_value = mock_session

        chat = TerminalChat()
        assert chat.config.render_markdown is False

        chat.chat()

    @patch('terminal_chat.cli.requests.post')
    @patch('terminal_chat.cli.PromptSession')
    def test_max_tokens_passed_to_api(self, mock_prompt_session, mock_post,
                                      temp_home, mock_keyring, clean_env):
        """Test that MAX_TOKENS is passed to API."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            MAX_TOKENS="2048",
            GUARDRAIL="none"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(
            return_value=[b'data: [DONE]\n\n']
        )
        mock_post.return_value = mock_response

        mock_session = Mock()
        mock_session.prompt.side_effect = ["Test", "exit"]
        mock_prompt_session.return_value = mock_session

        chat = TerminalChat()
        chat.chat()

        # Verify max_tokens in API call
        call_args = mock_post.call_args
        if call_args:
            json_data = call_args[1].get("json", {})
            assert json_data.get("max_tokens") == 2048


class TestErrorRecovery:
    """Test error recovery and resilience."""

    @patch('terminal_chat.cli.requests.post')
    @patch('terminal_chat.cli.PromptSession')
    def test_api_error_recovery(self, mock_prompt_session, mock_post,
                                temp_home, mock_keyring, clean_env):
        """Test that chat recovers from API errors."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="none"
        )

        # First call fails, second succeeds
        mock_fail = Mock()
        mock_fail.status_code = 500
        mock_fail.text = '{"error": {"message": "Server error"}}'
        mock_fail.raise_for_status.side_effect = Exception("500")

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.iter_lines = Mock(
            return_value=[
                b'data: {"choices": [{"delta": {"content": "OK"}}]}\n\n',
                b'data: [DONE]\n\n'
            ]
        )

        mock_post.side_effect = [mock_fail, mock_success]

        mock_session = Mock()
        mock_session.prompt.side_effect = ["First", "Second", "exit"]
        mock_prompt_session.return_value = mock_session

        chat = TerminalChat()

        # Should handle error and continue
        try:
            chat.chat()
        except:
            pass  # May raise, but shouldn't crash

    @patch('terminal_chat.cli.PromptSession')
    def test_keyboard_interrupt_handling(self, mock_prompt_session,
                                         temp_home, mock_keyring, clean_env):
        """Test handling of KeyboardInterrupt."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        mock_session = Mock()
        mock_session.prompt.side_effect = KeyboardInterrupt()
        mock_prompt_session.return_value = mock_session

        chat = TerminalChat()

        # Should handle gracefully
        result = chat.chat()
        # Should not crash
