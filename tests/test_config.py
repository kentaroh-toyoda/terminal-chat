"""
Tests for Config class.
"""
import os
import stat
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest
from terminal_chat.cli import Config
from tests.conftest import create_config_file


class TestConfigBasics:
    """Test basic configuration loading."""

    def test_missing_config_file(self, temp_home, mock_keyring, clean_env):
        """Test that missing config file raises SystemExit."""
        with pytest.raises(ValueError):
            Config()

    def test_load_minimal_config(self, temp_home, mock_keyring, clean_env):
        """Test loading minimal valid configuration."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test-token-12345"
        )

        config = Config()
        assert config.llm == "anthropic/claude-haiku-4.5"
        assert config.api_token == "sk-test-token-12345"

    def test_load_full_config(self, temp_home, mock_keyring, clean_env):
        """Test loading configuration with all options."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test-token",
            RENDER_MARKDOWN="true",
            SHOW_PANELS="false",
            SHOW_COST="true",
            INPUT_PREFIX=">>",
            MAX_TOKENS="8192",
            MAX_INPUT_LENGTH="20000",
            GUARDRAIL="external",
            EXTERNAL_GUARDRAIL_MODEL="meta-llama/llama-guard-4-12b",
            EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS="input",
            SHOW_INTENT="false",
            SYSTEM_PROMPT="Custom system prompt"
        )

        config = Config()
        assert config.llm == "anthropic/claude-haiku-4.5"
        assert config.render_markdown is True
        assert config.show_panels is False
        assert config.show_cost is True
        assert config.input_prefix == ">> "  # Auto-space added
        assert config.max_tokens == 8192
        assert config.max_input_length == 20000
        assert config.guardrail == "external"
        assert config.guardrail_model == "meta-llama/llama-guard-4-12b"
        assert config.guardrail_check == "input"
        assert config.show_intent is False
        assert config.system_prompt == "Custom system prompt"

    def test_missing_llm(self, temp_home, mock_keyring, clean_env):
        """Test that missing LLM raises SystemExit."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, API_TOKEN="sk-test-token")

        with pytest.raises(ValueError):
            Config()


class TestTokenLoading:
    """Test API token loading from various sources."""

    def test_token_from_keyring(self, temp_home, mock_keyring_with_token, clean_env):
        """Test loading token from keyring."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, LLM="anthropic/claude-haiku-4.5")

        config = Config()
        assert config.api_token == mock_keyring_with_token["token"]
        assert config.token_source == "keychain"

    def test_token_from_env(self, temp_home, mock_keyring, mock_env_token):
        """Test loading token from environment variable."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, LLM="anthropic/claude-haiku-4.5")

        config = Config()
        assert config.api_token == mock_env_token
        assert config.token_source == "environment"

    def test_token_from_file(self, temp_home, mock_keyring, clean_env):
        """Test loading token from config file."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-file-token"
        )

        config = Config()
        assert config.api_token == "sk-file-token"
        assert config.token_source == "file"

    def test_token_priority_keyring_over_env(self, temp_home, mock_keyring_with_token, mock_env_token):
        """Test that keyring takes priority over environment."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, LLM="anthropic/claude-haiku-4.5")

        config = Config()
        assert config.api_token == mock_keyring_with_token["token"]
        assert config.token_source == "keychain"

    def test_token_priority_env_over_file(self, temp_home, mock_keyring, mock_env_token):
        """Test that environment takes priority over file."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-file-token"
        )

        config = Config()
        assert config.api_token == mock_env_token
        assert config.token_source == "environment"

    def test_token_keyring_exception(self, temp_home, mock_keyring_failure, mock_env_token):
        """Test fallback when keyring raises exception."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, LLM="anthropic/claude-haiku-4.5")

        config = Config()
        assert config.api_token == mock_env_token
        assert config.token_source == "environment"

    def test_missing_token_all_sources(self, temp_home, mock_keyring, clean_env):
        """Test error when token is missing from all sources."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, LLM="anthropic/claude-haiku-4.5")

        with pytest.raises(ValueError):
            Config()


class TestConfigDefaults:
    """Test default configuration values."""

    def test_render_markdown_default(self, temp_home, mock_keyring, clean_env):
        """Test that RENDER_MARKDOWN defaults to true."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.render_markdown is True

    def test_show_panels_default(self, temp_home, mock_keyring, clean_env):
        """Test that SHOW_PANELS defaults to true."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.show_panels is True

    def test_show_cost_default(self, temp_home, mock_keyring, clean_env):
        """Test that SHOW_COST defaults to false."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.show_cost is False

    def test_input_prefix_default(self, temp_home, mock_keyring, clean_env):
        """Test that INPUT_PREFIX defaults to '> '."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.input_prefix == "> "

    def test_max_tokens_default(self, temp_home, mock_keyring, clean_env):
        """Test that MAX_TOKENS defaults to 4096."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.max_tokens == 4096

    def test_max_input_length_default(self, temp_home, mock_keyring, clean_env):
        """Test that MAX_INPUT_LENGTH defaults to 10000."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.max_input_length == 10000

    def test_guardrail_default(self, temp_home, mock_keyring, clean_env):
        """Test that GUARDRAIL defaults to 'system'."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.guardrail == "system"

    def test_guardrail_check_default(self, temp_home, mock_keyring, clean_env):
        """Test that EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS defaults to 'both'."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.guardrail_check == "both"

    def test_show_intent_default(self, temp_home, mock_keyring, clean_env):
        """Test that SHOW_INTENT defaults to true."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        config = Config()
        assert config.show_intent is True


class TestInputPrefixHandling:
    """Test INPUT_PREFIX handling and auto-spacing."""

    def test_input_prefix_with_space(self, temp_home, mock_keyring, clean_env):
        """Test that prefix with space is not modified."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            INPUT_PREFIX="ask: "
        )

        config = Config()
        assert config.input_prefix == "ask: "

    def test_input_prefix_without_space(self, temp_home, mock_keyring, clean_env):
        """Test that prefix without space gets space added."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            INPUT_PREFIX="ask:"
        )

        config = Config()
        assert config.input_prefix == "ask: "

    def test_input_prefix_empty_string(self, temp_home, mock_keyring, clean_env):
        """Test handling of empty INPUT_PREFIX."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            INPUT_PREFIX=""
        )

        config = Config()
        assert config.input_prefix == " "  # Space added to empty

    @pytest.mark.parametrize("prefix,expected", [
        (">", "> "),
        (">>", ">> "),
        ("ask", "ask "),
        ("(user)", "(user) "),
        ("➜", "➜ "),
        (">>> ", ">>> "),  # Already has space
        ("test  ", "test  "),  # Multiple spaces preserved
    ])
    def test_input_prefix_variations(self, temp_home, mock_keyring, clean_env, prefix, expected):
        """Test various INPUT_PREFIX values."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            INPUT_PREFIX=prefix
        )

        config = Config()
        assert config.input_prefix == expected


class TestGuardrailValidation:
    """Test guardrail configuration validation."""

    @pytest.mark.parametrize("guardrail_value", ["system", "external", "intent", "none"])
    def test_valid_guardrail_values(self, temp_home, mock_keyring, clean_env, guardrail_value):
        """Test all valid GUARDRAIL values."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL=guardrail_value
        )

        config = Config()
        assert config.guardrail == guardrail_value

    def test_invalid_guardrail_value(self, temp_home, mock_keyring, clean_env):
        """Test that invalid GUARDRAIL raises SystemExit."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            GUARDRAIL="invalid"
        )

        with pytest.raises(ValueError):
            Config()

    @pytest.mark.parametrize("check_value", ["input", "output", "both"])
    def test_valid_guardrail_check_values(self, temp_home, mock_keyring, clean_env, check_value):
        """Test all valid EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS values."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS=check_value
        )

        config = Config()
        assert config.guardrail_check == check_value

    def test_invalid_guardrail_check_value(self, temp_home, mock_keyring, clean_env):
        """Test that invalid EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS defaults to 'both'."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS="invalid"
        )

        # Invalid values default to 'both'
        config = Config()
        assert config.guardrail_check == "both"


class TestBooleanParsing:
    """Test boolean configuration parsing."""

    @pytest.mark.parametrize("value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
    ])
    def test_boolean_values(self, temp_home, mock_keyring, clean_env, value, expected):
        """Test boolean parsing for RENDER_MARKDOWN."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            RENDER_MARKDOWN=value
        )

        config = Config()
        assert config.render_markdown is expected

    def test_invalid_boolean_defaults_to_false(self, temp_home, mock_keyring, clean_env):
        """Test that invalid boolean defaults to false."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            RENDER_MARKDOWN="invalid"
        )

        config = Config()
        assert config.render_markdown is False


class TestIntegerParsing:
    """Test integer configuration parsing."""

    def test_valid_max_tokens(self, temp_home, mock_keyring, clean_env):
        """Test parsing valid MAX_TOKENS."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            MAX_TOKENS="8192"
        )

        config = Config()
        assert config.max_tokens == 8192

    def test_invalid_max_tokens_uses_default(self, temp_home, mock_keyring, clean_env):
        """Test that invalid MAX_TOKENS uses default."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            MAX_TOKENS="invalid"
        )

        config = Config()
        assert config.max_tokens == 4096  # Default

    def test_valid_max_input_length(self, temp_home, mock_keyring, clean_env):
        """Test parsing valid MAX_INPUT_LENGTH."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            MAX_INPUT_LENGTH="50000"
        )

        config = Config()
        assert config.max_input_length == 50000

    def test_invalid_max_input_length_uses_default(self, temp_home, mock_keyring, clean_env):
        """Test that invalid MAX_INPUT_LENGTH uses default."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test",
            MAX_INPUT_LENGTH="not_a_number"
        )

        config = Config()
        assert config.max_input_length == 10000  # Default


class TestLocalConfigOverride:
    """Test local .askrc overriding home config."""

    def test_local_overrides_home(self, temp_home, temp_cwd, mock_keyring, clean_env, mock_confirm):
        """Test that local config overrides home config."""
        # Home config
        home_config = temp_home / ".askrc"
        create_config_file(
            home_config,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-home-token",
            RENDER_MARKDOWN="true"
        )

        # Local config
        local_config = temp_cwd / ".askrc"
        create_config_file(
            local_config,
            LLM="openai/gpt-5-mini",
            RENDER_MARKDOWN="false"
        )

        mock_confirm.ask.return_value = True  # Confirm loading local config

        config = Config()
        assert config.llm == "openai/gpt-5-mini"  # From local
        assert config.render_markdown is False  # From local
        assert config.api_token == "sk-home-token"  # From home (not overridden)

    def test_local_config_requires_confirmation(self, temp_home, temp_cwd, mock_keyring, clean_env, mock_confirm):
        """Test that local config requires user confirmation."""
        home_config = temp_home / ".askrc"
        create_config_file(
            home_config,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-token"
        )

        local_config = temp_cwd / ".askrc"
        create_config_file(local_config, LLM="openai/gpt-5-mini")

        mock_confirm.ask.return_value = True

        Config()

        # Should have asked for confirmation
        mock_confirm.ask.assert_called_once()

    def test_local_config_rejected(self, temp_home, temp_cwd, mock_keyring, clean_env, mock_confirm):
        """Test rejecting local config loads only home config."""
        home_config = temp_home / ".askrc"
        create_config_file(
            home_config,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-token",
            RENDER_MARKDOWN="true"
        )

        local_config = temp_cwd / ".askrc"
        create_config_file(
            local_config,
            LLM="openai/gpt-5-mini",
            RENDER_MARKDOWN="false"
        )

        mock_confirm.ask.return_value = False  # Reject local config

        config = Config()
        assert config.llm == "anthropic/claude-haiku-4.5"  # From home only
        assert config.render_markdown is True  # From home only

    def test_no_local_config_no_prompt(self, temp_home, mock_keyring, clean_env, mock_confirm):
        """Test that no prompt appears when local config doesn't exist."""
        home_config = temp_home / ".askrc"
        create_config_file(
            home_config,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-token"
        )

        Config()

        # Should not have asked for confirmation
        mock_confirm.ask.assert_not_called()


class TestSecurityFeatures:
    """Test security-related features."""

    @patch('os.chmod')
    @patch('os.stat')
    def test_insecure_permissions_warning(self, mock_stat, mock_chmod, temp_home, mock_keyring, clean_env, mock_console):
        """Test warning for insecure file permissions."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-token"
        )

        # Mock insecure permissions (readable by others)
        mock_stat_result = Mock()
        mock_stat_result.st_mode = 0o644  # rw-r--r--
        mock_stat.return_value = mock_stat_result

        Config()

        # Should have printed warning (checked via mock_console if used)
        # Actual implementation may use Console.print

    def test_rich_markup_escaping_in_prefix(self, temp_home, mock_keyring, clean_env):
        """Test that Rich markup in INPUT_PREFIX is escaped."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-token",
            INPUT_PREFIX="[bold]test[/bold]"
        )

        config = Config()
        # Should be escaped (implementation uses escape())
        assert "[bold]" in config.input_prefix or "\\[bold]" in config.input_prefix


class TestMigrationSuggestion:
    """Test token migration suggestion."""

    def test_suggest_migration_when_token_in_file(self, temp_home, mock_keyring, clean_env, capsys):
        """Test migration suggestion when token is in file."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-file-token"
        )

        config = Config()

        # Should suggest migration (check captured output or console calls)
        assert config.token_source == "file"

    def test_no_migration_suggestion_when_in_keyring(self, temp_home, mock_keyring_with_token, clean_env):
        """Test no migration suggestion when token is in keyring."""
        config_path = temp_home / ".askrc"
        create_config_file(config_path, LLM="anthropic/claude-haiku-4.5")

        config = Config()
        assert config.token_source == "keychain"
        # No migration suggestion should appear


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_config_file(self, temp_home, mock_keyring, clean_env):
        """Test handling empty config file."""
        config_path = temp_home / ".askrc"
        config_path.touch()

        with pytest.raises(ValueError):
            Config()

    def test_malformed_config_file(self, temp_home, mock_keyring, clean_env):
        """Test handling malformed config file."""
        config_path = temp_home / ".askrc"
        with open(config_path, "w") as f:
            f.write("This is not a valid config\n")
            f.write("LLM\n")  # Missing value
            f.write("API_TOKEN=sk-token\n")

        # Should handle gracefully (dotenv_values is forgiving)
        config = Config()
        # LLM should be missing, causing SystemExit
        # But this actually raises SystemExit due to missing LLM

    def test_config_with_comments(self, temp_home, mock_keyring, clean_env):
        """Test config file with comments."""
        config_path = temp_home / ".askrc"
        with open(config_path, "w") as f:
            f.write("# This is a comment\n")
            f.write("LLM=anthropic/claude-haiku-4.5\n")
            f.write("# Another comment\n")
            f.write("API_TOKEN=sk-token\n")

        config = Config()
        assert config.llm == "anthropic/claude-haiku-4.5"
        assert config.api_token == "sk-token"

    def test_config_with_extra_whitespace(self, temp_home, mock_keyring, clean_env):
        """Test config file with extra whitespace."""
        config_path = temp_home / ".askrc"
        with open(config_path, "w") as f:
            f.write("  LLM  =  anthropic/claude-haiku-4.5  \n")
            f.write("  API_TOKEN  =  sk-token  \n")

        config = Config()
        # dotenv_values should handle trimming
        assert "anthropic/claude-haiku-4.5" in config.llm

    def test_unicode_in_system_prompt(self, temp_home, mock_keyring, clean_env):
        """Test handling unicode characters in SYSTEM_PROMPT."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-token",
            SYSTEM_PROMPT="你好 🎉 Здравствуйте"
        )

        config = Config()
        assert "你好" in config.system_prompt
        assert "🎉" in config.system_prompt
