"""
Tests for GuardrailChecker class.
"""
import json
from unittest.mock import Mock, patch, MagicMock
import pytest
from terminal_chat.cli import GuardrailChecker, Config
from tests.conftest import create_config_file


@pytest.fixture
def mock_config_system(temp_home, mock_keyring, clean_env):
    """Create a config with system guardrail."""
    config_path = temp_home / ".askrc"
    create_config_file(
        config_path,
        LLM="anthropic/claude-haiku-4.5",
        API_TOKEN="sk-test",
        GUARDRAIL="system"
    )
    return Config()


@pytest.fixture
def mock_config_external(temp_home, mock_keyring, clean_env):
    """Create a config with external guardrail."""
    config_path = temp_home / ".askrc"
    create_config_file(
        config_path,
        LLM="anthropic/claude-haiku-4.5",
        API_TOKEN="sk-test",
        GUARDRAIL="external",
        EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS="both"
    )
    return Config()


@pytest.fixture
def mock_config_intent(temp_home, mock_keyring, clean_env):
    """Create a config with intent guardrail."""
    config_path = temp_home / ".askrc"
    create_config_file(
        config_path,
        LLM="anthropic/claude-haiku-4.5",
        API_TOKEN="sk-test",
        GUARDRAIL="intent",
        SHOW_INTENT="true"
    )
    return Config()


@pytest.fixture
def mock_config_none(temp_home, mock_keyring, clean_env):
    """Create a config with no guardrail."""
    config_path = temp_home / ".askrc"
    create_config_file(
        config_path,
        LLM="anthropic/claude-haiku-4.5",
        API_TOKEN="sk-test",
        GUARDRAIL="none"
    )
    return Config()


class TestGuardrailCheckerInit:
    """Test GuardrailChecker initialization."""

    def test_init_system(self, mock_config_system, mock_console):
        """Test initialization with system guardrail."""
        checker = GuardrailChecker(mock_config_system, mock_config_system.api_token, mock_console)

        assert checker.config.guardrail == "system"

    def test_init_external(self, mock_config_external, mock_console):
        """Test initialization with external guardrail."""
        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)

        assert checker.config.guardrail == "external"
        assert checker.config.guardrail_check == "both"

    def test_init_intent(self, mock_config_intent, mock_console):
        """Test initialization with intent guardrail."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        assert checker.config.guardrail == "intent"

    def test_init_none(self, mock_config_none, mock_console):
        """Test initialization with no guardrail."""
        checker = GuardrailChecker(mock_config_none, mock_config_none.api_token, mock_console)

        assert checker.config.guardrail == "none"


class TestSystemGuardrail:
    """Test system guardrail mode."""

    def test_check_input_always_passes(self, mock_config_system, mock_console):
        """Test that system guardrail always passes input checks."""
        checker = GuardrailChecker(mock_config_system, mock_config_system.api_token, mock_console)

        allowed, reason = checker.check_input("Safe message")
        assert allowed is True
        assert reason == ""

        allowed, reason = checker.check_input("Potentially unsafe message")
        assert allowed is True
        assert reason == ""

    def test_check_output_always_passes(self, mock_config_system, mock_console):
        """Test that system guardrail always passes output checks."""
        checker = GuardrailChecker(mock_config_system, mock_config_system.api_token, mock_console)

        allowed, reason = checker.check_output("Safe response")
        assert allowed is True
        assert reason == ""


class TestNoneGuardrail:
    """Test disabled guardrail mode."""

    def test_check_input_bypassed(self, mock_config_none, mock_console):
        """Test that no guardrail bypasses all input checks."""
        checker = GuardrailChecker(mock_config_none, mock_config_none.api_token, mock_console)

        allowed, reason = checker.check_input("Any message")
        assert allowed is True
        assert reason == ""

    def test_check_output_bypassed(self, mock_config_none, mock_console):
        """Test that no guardrail bypasses all output checks."""
        checker = GuardrailChecker(mock_config_none, mock_config_none.api_token, mock_console)

        allowed, reason = checker.check_output("Any response")
        assert allowed is True
        assert reason == ""


class TestExternalGuardrail:
    """Test external guardrail (Llama Guard) mode."""

    @patch('terminal_chat.cli.requests.post')
    def test_check_input_safe(self, mock_post, mock_config_external, mock_console):
        """Test external guardrail with safe input."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        allowed, reason = checker.check_input("Hello, how are you?")

        assert allowed is True
        assert reason == ""

    @patch('terminal_chat.cli.requests.post')
    def test_check_input_unsafe(self, mock_post, mock_config_external, mock_console):
        """Test external guardrail with unsafe input."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "unsafe\nS3: Violent Crimes"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        allowed, reason = checker.check_input("Harmful content")

        assert allowed is False
        # Reason should be formatted as "Sex-Related Crimes (S3)"
        assert "S3" in reason and "Crimes" in reason

    @patch('terminal_chat.cli.requests.post')
    def test_check_output_safe(self, mock_post, mock_config_external, mock_console):
        """Test external guardrail with safe output."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        allowed, reason = checker.check_output("Here is helpful information.")

        assert allowed is True
        assert reason == ""

    @patch('terminal_chat.cli.requests.post')
    def test_check_only_input(self, mock_post, temp_home, mock_keyring, clean_env, mock_console):
        """Test checking only input when configured."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="external",
            EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS="input"
        )
        config = Config()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(config, config.api_token, mock_console)

        # Input should be checked
        allowed, reason = checker.check_input("Test")
        assert mock_post.called

        mock_post.reset_mock()

        # Output should NOT be checked
        allowed, reason = checker.check_output("Test")
        assert allowed is True
        assert not mock_post.called

    @patch('terminal_chat.cli.requests.post')
    def test_check_only_output(self, mock_post, temp_home, mock_keyring, clean_env, mock_console):
        """Test checking only output when configured."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="external",
            EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS="output"
        )
        config = Config()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(config, config.api_token, mock_console)

        # Input should NOT be checked
        allowed, reason = checker.check_input("Test")
        assert allowed is True
        assert not mock_post.called

        # Output should be checked
        allowed, reason = checker.check_output("Test")
        assert mock_post.called

    @patch('terminal_chat.cli.requests.post')
    def test_external_api_failure(self, mock_post, mock_config_external, mock_console, mock_confirm):
        """Test handling of external API failure."""
        mock_post.side_effect = Exception("API Error")
        mock_confirm.ask.return_value = True  # User continues

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        allowed, reason = checker.check_input("Test")

        # Should ask user and allow if they confirm
        assert mock_confirm.ask.called
        assert allowed is True

    @patch('terminal_chat.cli.requests.post')
    def test_external_api_failure_user_stops(self, mock_post, mock_config_external, mock_console, mock_confirm):
        """Test handling when user chooses to stop after API failure."""
        mock_post.side_effect = Exception("API Error")
        mock_confirm.ask.return_value = False  # User stops

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        allowed, reason = checker.check_input("Test")

        assert allowed is False
        assert "failed" in reason.lower() or "error" in reason.lower()

    @patch('terminal_chat.cli.requests.post')
    def test_llama_guard_prompt_format(self, mock_post, mock_config_external, mock_console):
        """Test that Llama Guard prompt is formatted correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        checker.check_input("Test message")

        # Verify the API call
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]

        # Should have special Llama Guard format
        assert len(messages) > 0
        assert any("Test message" in str(msg) for msg in messages)

    @patch('terminal_chat.cli.requests.post')
    def test_external_timeout(self, mock_post, mock_config_external, mock_console):
        """Test handling of external guardrail timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)

        with patch('terminal_chat.cli.Confirm') as mock_confirm:
            mock_confirm.ask.return_value = True
            allowed, reason = checker.check_input("Test")

            # Should handle timeout gracefully
            assert mock_confirm.ask.called


class TestIntentGuardrail:
    """Test intent-based guardrail mode."""

    def test_parse_intent_appropriate(self, mock_console, mock_config_intent):
        """Test parsing appropriate intent response."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = '''{"intent": "User asking about weather", "appropriate": true, "reason": ""}
The weather today is sunny.'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        assert allowed is True
        assert "weather" in intent_summary.lower()
        assert "sunny" in actual_response

    def test_parse_intent_inappropriate(self, mock_console, mock_config_intent):
        """Test parsing inappropriate intent response."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = '''{"intent": "User requesting harmful information", "appropriate": false, "reason": "Violates content policy"}
'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        assert allowed is False
        assert "harmful" in intent_summary.lower() or "policy" in intent_summary.lower()

    def test_parse_intent_malformed_json(self, mock_console, mock_config_intent):
        """Test handling malformed JSON in intent response."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = '''This is not JSON
Just a regular response.'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        # Should fallback gracefully
        assert allowed is True  # Default to allowing
        assert "regular response" in actual_response or "not found" in intent_summary.lower()

    def test_parse_intent_partial_json(self, mock_console, mock_config_intent):
        """Test handling partial JSON in intent response."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = '''{"intent": "Incomplete'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        # Should handle gracefully
        assert isinstance(allowed, bool)

    def test_parse_intent_with_newlines(self, mock_console, mock_config_intent):
        """Test parsing intent response with embedded newlines."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = '''{"intent": "Multi-line\\nintent", "appropriate": true, "reason": ""}
Response line 1
Response line 2
Response line 3'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        assert allowed is True
        assert "Response line 1" in actual_response
        assert "Response line 2" in actual_response

    def test_parse_intent_json_in_middle(self, mock_console, mock_config_intent):
        """Test extracting JSON from middle of response."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = '''Some preamble text
{"intent": "User question", "appropriate": true, "reason": ""}
The actual answer follows.'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        assert allowed is True
        assert "actual answer" in actual_response.lower()
        assert "preamble" not in actual_response.lower()

    def test_parse_intent_missing_fields(self, mock_console, mock_config_intent):
        """Test handling JSON with missing required fields."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        # Missing 'appropriate' field
        response = '''{"intent": "Some intent", "reason": ""}
Response text'''

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        # Should have defaults
        assert isinstance(allowed, bool)
        assert isinstance(intent_summary, str)

    def test_parse_intent_empty_response(self, mock_console, mock_config_intent):
        """Test handling empty response."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = ""

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        assert isinstance(allowed, bool)
        assert isinstance(intent_summary, str)
        assert actual_response == ""

    @pytest.mark.parametrize("appropriate_value,expected_allowed", [
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        (1, True),
        (0, False),
    ])
    def test_parse_intent_boolean_variations(self, mock_config_intent, appropriate_value, expected_allowed):
        """Test handling various boolean representations."""
        checker = GuardrailChecker(mock_config_intent, mock_config_intent.api_token, mock_console)

        response = f'{{"intent": "Test", "appropriate": {json.dumps(appropriate_value)}, "reason": ""}}\nResponse'

        allowed, intent_summary, actual_response = checker.parse_intent_response(response)

        assert allowed == expected_allowed


class TestGuardrailEdgeCases:
    """Test edge cases in guardrail checking."""

    def test_empty_input(self, mock_config_system, mock_console):
        """Test checking empty input."""
        checker = GuardrailChecker(mock_config_system, mock_config_system.api_token, mock_console)

        allowed, reason = checker.check_input("")
        assert allowed is True

    def test_very_long_input(self, mock_config_system, mock_console):
        """Test checking very long input."""
        checker = GuardrailChecker(mock_config_system, mock_config_system.api_token, mock_console)

        long_text = "A" * 100000
        allowed, reason = checker.check_input(long_text)
        assert allowed is True

    def test_unicode_input(self, mock_config_system, mock_console):
        """Test checking unicode input."""
        checker = GuardrailChecker(mock_config_system, mock_config_system.api_token, mock_console)

        unicode_text = "你好 🎉 Здравствуйте مرحبا"
        allowed, reason = checker.check_input(unicode_text)
        assert allowed is True

    @patch('terminal_chat.cli.requests.post')
    def test_special_characters_in_external(self, mock_post, mock_config_external, mock_console):
        """Test special characters with external guardrail."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        checker = GuardrailChecker(mock_config_external, mock_config_external.api_token, mock_console)
        text = "Test with special chars: @#$%^&*()"

        allowed, reason = checker.check_input(text)

        # Should handle special characters
        call_args = mock_post.call_args
        assert call_args is not None


class TestGuardrailModeTransitions:
    """Test behavior across different guardrail modes."""

    def test_different_modes_different_behavior(self):
        """Test that different modes produce different behavior."""
        # System mode
        system_config = Mock()
        system_config.guardrail = "system"
        system_checker = GuardrailChecker(system_config)

        # None mode
        none_config = Mock()
        none_config.guardrail = "none"
        none_checker = GuardrailChecker(none_config)

        # Both should pass input checks (but for different reasons)
        assert system_checker.check_input("Test")[0] is True
        assert none_checker.check_input("Test")[0] is True

    @patch('terminal_chat.cli.requests.post')
    def test_mode_affects_api_calls(self, mock_post):
        """Test that mode determines whether API is called."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "safe"}}]
        }
        mock_post.return_value = mock_response

        # System mode - no API calls
        system_config = Mock()
        system_config.guardrail = "system"
        system_checker = GuardrailChecker(system_config)
        system_checker.check_input("Test")

        assert not mock_post.called

        # External mode - API calls
        external_config = Mock()
        external_config.guardrail = "external"
        external_config.guardrail_check = "input"
        external_config.guardrail_model = "test-model"
        external_config.api_token = "test-token"
        external_checker = GuardrailChecker(external_config)
        external_checker.check_input("Test")

        assert mock_post.called
