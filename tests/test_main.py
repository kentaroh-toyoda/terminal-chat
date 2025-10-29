"""
Tests for main() entry point.
"""
import pytest
from unittest.mock import Mock, patch, call
from terminal_chat.cli import main
from tests.conftest import create_config_file


class TestMainEntry:
    """Test main() entry point."""

    @patch('terminal_chat.cli.TerminalChat')
    @patch('terminal_chat.cli.Config')
    def test_main_no_args(self, mock_config_class, mock_chat_class,
                          temp_home, mock_keyring, clean_env):
        """Test main with no arguments."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_chat = Mock()
        mock_chat.chat.return_value = None
        mock_chat_class.return_value = mock_chat

        with patch('sys.argv', ['ask']):
            exit_code = main()

        assert exit_code == 0
        mock_chat.chat.assert_called_once_with(None)

    @patch('terminal_chat.cli.TerminalChat')
    @patch('terminal_chat.cli.Config')
    def test_main_with_message(self, mock_config_class, mock_chat_class,
                               temp_home, mock_keyring, clean_env):
        """Test main with initial message."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_chat = Mock()
        mock_chat.chat.return_value = None
        mock_chat_class.return_value = mock_chat

        with patch('sys.argv', ['ask', 'Hello', 'world']):
            exit_code = main()

        assert exit_code == 0
        mock_chat.chat.assert_called_once_with("Hello world")

    @patch('terminal_chat.cli.SetupWizard')
    def test_main_setup_flag(self, mock_wizard_class, temp_home):
        """Test main with --setup flag."""
        mock_wizard = Mock()
        mock_wizard.run.return_value = True
        mock_wizard_class.return_value = mock_wizard

        with patch('sys.argv', ['ask', '--setup']):
            with patch('terminal_chat.cli.Config'):
                with patch('terminal_chat.cli.TerminalChat'):
                    exit_code = main()

        mock_wizard.run.assert_called_once()

    @patch('terminal_chat.cli.SetupWizard')
    def test_main_setup_short_flag(self, mock_wizard_class, temp_home):
        """Test main with -s flag."""
        mock_wizard = Mock()
        mock_wizard.run.return_value = True
        mock_wizard_class.return_value = mock_wizard

        with patch('sys.argv', ['ask', '-s']):
            with patch('terminal_chat.cli.Config'):
                with patch('terminal_chat.cli.TerminalChat'):
                    exit_code = main()

        mock_wizard.run.assert_called_once()

    @patch('terminal_chat.cli.Config')
    def test_main_missing_config_triggers_setup(self, mock_config_class,
                                                 temp_home, mock_keyring, clean_env):
        """Test that missing config triggers setup wizard."""
        mock_config_class.side_effect = SystemExit(1)

        with patch('terminal_chat.cli.SetupWizard') as mock_wizard_class:
            mock_wizard = Mock()
            mock_wizard.run.return_value = True
            mock_wizard_class.return_value = mock_wizard

            with patch('sys.argv', ['ask']):
                with patch('terminal_chat.cli.TerminalChat'):
                    exit_code = main()

            mock_wizard.run.assert_called_once()

    def test_main_keyboard_interrupt(self, temp_home, mock_keyring, clean_env):
        """Test handling KeyboardInterrupt."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        with patch('terminal_chat.cli.TerminalChat') as mock_chat_class:
            mock_chat = Mock()
            mock_chat.chat.side_effect = KeyboardInterrupt()
            mock_chat_class.return_value = mock_chat

            with patch('sys.argv', ['ask']):
                exit_code = main()

            assert exit_code == 0

    def test_main_generic_exception(self, temp_home, mock_keyring, clean_env):
        """Test handling generic exceptions."""
        config_path = temp_home / ".askrc"
        create_config_file(
            config_path,
            LLM="anthropic/claude-haiku-4.5",
            API_TOKEN="sk-test"
        )

        with patch('terminal_chat.cli.TerminalChat') as mock_chat_class:
            mock_chat = Mock()
            mock_chat.chat.side_effect = Exception("Test error")
            mock_chat_class.return_value = mock_chat

            with patch('sys.argv', ['ask']):
                exit_code = main()

            assert exit_code == 1
