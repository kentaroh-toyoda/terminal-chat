"""
Shared pytest fixtures and configuration for terminal-chat tests.
"""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock
import pytest


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_configs_dir(fixtures_dir):
    """Return the path to sample config files."""
    return fixtures_dir / "sample_configs"


@pytest.fixture
def api_responses(fixtures_dir):
    """Load and return API response fixtures."""
    with open(fixtures_dir / "api_responses.json", "r") as f:
        return json.load(f)


# ============================================================================
# Config File Fixtures
# ============================================================================

@pytest.fixture
def valid_full_config(sample_configs_dir):
    """Return path to a valid full config file."""
    return sample_configs_dir / "valid_full.askrc"


@pytest.fixture
def minimal_config(sample_configs_dir):
    """Return path to a minimal config file."""
    return sample_configs_dir / "minimal.askrc"


@pytest.fixture
def no_token_config(sample_configs_dir):
    """Return path to a config file without token."""
    return sample_configs_dir / "no_token.askrc"


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    """Create a temporary home directory and patch Path.home()."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


@pytest.fixture
def temp_cwd(tmp_path, monkeypatch):
    """Create a temporary working directory and change to it."""
    cwd = tmp_path / "project"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    return cwd


# ============================================================================
# Keyring Mocks
# ============================================================================

@pytest.fixture
def mock_keyring(monkeypatch):
    """Mock keyring module with successful operations."""
    mock_get = Mock(return_value=None)
    mock_set = Mock()

    monkeypatch.setattr("terminal_chat.cli.keyring.get_password", mock_get)
    monkeypatch.setattr("terminal_chat.cli.keyring.set_password", mock_set)

    return {"get_password": mock_get, "set_password": mock_set}


@pytest.fixture
def mock_keyring_with_token(monkeypatch):
    """Mock keyring that returns a token."""
    token = "sk-test-keyring-token-12345"
    mock_get = Mock(return_value=token)
    mock_set = Mock()

    monkeypatch.setattr("terminal_chat.cli.keyring.get_password", mock_get)
    monkeypatch.setattr("terminal_chat.cli.keyring.set_password", mock_set)

    return {"get_password": mock_get, "set_password": mock_set, "token": token}


@pytest.fixture
def mock_keyring_failure(monkeypatch):
    """Mock keyring that raises exceptions."""
    mock_get = Mock(side_effect=Exception("Keyring unavailable"))
    mock_set = Mock(side_effect=Exception("Keyring unavailable"))

    monkeypatch.setattr("terminal_chat.cli.keyring.get_password", mock_get)
    monkeypatch.setattr("terminal_chat.cli.keyring.set_password", mock_set)

    return {"get_password": mock_get, "set_password": mock_set}


# ============================================================================
# Environment Mocks
# ============================================================================

@pytest.fixture
def mock_env_token(monkeypatch):
    """Set ASK_API_TOKEN environment variable."""
    token = "sk-test-env-token-67890"
    monkeypatch.setenv("ASK_API_TOKEN", token)
    return token


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all ASK_* environment variables."""
    monkeypatch.delenv("ASK_API_TOKEN", raising=False)


# ============================================================================
# API Mocks
# ============================================================================

@pytest.fixture
def mock_requests_post(monkeypatch):
    """Mock requests.post for API calls."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_lines = Mock(return_value=[])
    mock_response.json = Mock(return_value={})

    mock_post = Mock(return_value=mock_response)
    monkeypatch.setattr("terminal_chat.cli.requests.post", mock_post)

    return {"post": mock_post, "response": mock_response}


@pytest.fixture
def mock_streaming_response(api_responses):
    """Create a mock response for streaming chat."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_lines = Mock(
        return_value=[line.encode() for line in api_responses["chat_success_stream"]]
    )
    return mock_response


@pytest.fixture
def mock_error_response():
    """Create a mock error response."""
    def _make_error(status_code, message):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = json.dumps({"error": {"message": message}})
        mock_response.raise_for_status = Mock(side_effect=Exception(f"HTTP {status_code}"))
        return mock_response
    return _make_error


# ============================================================================
# Keyboard/Input Mocks
# ============================================================================

@pytest.fixture
def mock_stdin(monkeypatch):
    """Mock sys.stdin for input simulation."""
    mock = Mock()
    mock.fileno = Mock(return_value=0)
    mock.read = Mock(return_value="")
    monkeypatch.setattr("sys.stdin", mock)
    return mock


@pytest.fixture
def mock_select_esc(monkeypatch):
    """Mock select.select to simulate ESC key press."""
    mock_stdin = Mock()
    mock_stdin.read = Mock(return_value="\x1b")  # ESC key

    monkeypatch.setattr("select.select", Mock(return_value=([mock_stdin], [], [])))
    monkeypatch.setattr("sys.stdin", mock_stdin)
    return mock_stdin


@pytest.fixture
def mock_select_no_input(monkeypatch):
    """Mock select.select to return no input."""
    monkeypatch.setattr("select.select", Mock(return_value=([], [], [])))


@pytest.fixture
def mock_termios(monkeypatch):
    """Mock termios module for terminal control."""
    mock_tcgetattr = Mock(return_value=[0, 0, 0, 0, 0, 0, []])
    mock_tcsetattr = Mock()

    monkeypatch.setattr("terminal_chat.cli.termios.tcgetattr", mock_tcgetattr)
    monkeypatch.setattr("terminal_chat.cli.termios.tcsetattr", mock_tcsetattr)
    monkeypatch.setattr("terminal_chat.cli.termios.TCSADRAIN", 2)

    return {"tcgetattr": mock_tcgetattr, "tcsetattr": mock_tcsetattr}


@pytest.fixture
def mock_tty(monkeypatch):
    """Mock tty module."""
    mock_setcbreak = Mock()
    monkeypatch.setattr("terminal_chat.cli.tty.setcbreak", mock_setcbreak)
    return {"setcbreak": mock_setcbreak}


# ============================================================================
# Console/UI Mocks
# ============================================================================

@pytest.fixture
def mock_console(monkeypatch):
    """Mock Rich Console."""
    from terminal_chat.cli import Console

    mock = Mock(spec=Console)
    mock.print = Mock()
    monkeypatch.setattr("terminal_chat.cli.Console", Mock(return_value=mock))

    return mock


@pytest.fixture
def mock_prompt_session(monkeypatch):
    """Mock PromptSession for user input."""
    mock_session = Mock()
    mock_session.prompt = Mock(return_value="test input")

    monkeypatch.setattr(
        "terminal_chat.cli.PromptSession",
        Mock(return_value=mock_session)
    )

    return mock_session


@pytest.fixture
def mock_confirm(monkeypatch):
    """Mock rich.prompt.Confirm."""
    mock = Mock()
    mock.ask = Mock(return_value=True)
    monkeypatch.setattr("terminal_chat.cli.Confirm", mock)
    return mock


@pytest.fixture
def mock_prompt(monkeypatch):
    """Mock rich.prompt.Prompt."""
    mock = Mock()
    mock.ask = Mock(return_value="test response")
    monkeypatch.setattr("terminal_chat.cli.Prompt", mock)
    return mock


# ============================================================================
# Platform Mocks
# ============================================================================

@pytest.fixture
def mock_unix_platform(monkeypatch):
    """Mock sys.platform to return Unix-like system."""
    monkeypatch.setattr("sys.platform", "darwin")


@pytest.fixture
def mock_windows_platform(monkeypatch):
    """Mock sys.platform to return Windows."""
    monkeypatch.setattr("sys.platform", "win32")


# ============================================================================
# Signal Mocks
# ============================================================================

@pytest.fixture
def mock_signal(monkeypatch):
    """Mock signal.signal for SIGINT handling."""
    mock_signal_fn = Mock()
    monkeypatch.setattr("signal.signal", mock_signal_fn)
    monkeypatch.setattr("signal.SIGINT", 2)
    return mock_signal_fn


# ============================================================================
# Helper Functions
# ============================================================================

def create_config_file(path: Path, **kwargs):
    """Helper to create a config file with specified options."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        for key, value in kwargs.items():
            f.write(f"{key}={value}\n")

    return path


def create_mock_stream_response(chunks: list):
    """Helper to create a mock streaming response from a list of chunks."""
    mock_response = Mock()
    mock_response.status_code = 200

    formatted_chunks = []
    for chunk in chunks:
        if isinstance(chunk, dict):
            formatted_chunks.append(f"data: {json.dumps(chunk)}\n\n".encode())
        else:
            formatted_chunks.append(chunk.encode())

    mock_response.iter_lines = Mock(return_value=formatted_chunks)
    return mock_response


# Expose helper functions for import
__all__ = [
    "create_config_file",
    "create_mock_stream_response",
]
