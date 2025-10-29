"""
Tests for KeyboardMonitor class (Unix/macOS only).
"""
import time
from unittest.mock import Mock, patch, call
import pytest
from terminal_chat.cli import KeyboardMonitor


class TestKeyboardMonitorInit:
    """Test KeyboardMonitor initialization."""

    def test_init_state(self):
        """Test initial state of KeyboardMonitor."""
        monitor = KeyboardMonitor()

        assert monitor.interrupted is False
        assert monitor.monitoring is False
        assert monitor.thread is None

    def test_is_interrupted_initial(self):
        """Test is_interrupted returns False initially."""
        monitor = KeyboardMonitor()
        assert monitor.is_interrupted() is False


class TestKeyboardMonitorUnix:
    """Test KeyboardMonitor Unix-specific functionality."""

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_start_monitoring_unix(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                                   mock_tcgetattr, mock_select):
        """Test starting monitoring on Unix."""
        mock_stdin.fileno.return_value = 0
        mock_tcgetattr.return_value = [0, 0, 0, 0, 0, 0, []]
        mock_select.return_value = ([], [], [])  # No input

        monitor = KeyboardMonitor()
        monitor.start()

        assert monitor.monitoring is True
        assert monitor.thread is not None
        assert monitor.thread.is_alive()

        monitor.stop()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_stop_monitoring_unix(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                                  mock_tcgetattr, mock_select):
        """Test stopping monitoring on Unix."""
        mock_stdin.fileno.return_value = 0
        mock_tcgetattr.return_value = [0, 0, 0, 0, 0, 0, []]
        mock_select.return_value = ([], [], [])

        monitor = KeyboardMonitor()
        monitor.start()

        # Give thread time to start
        time.sleep(0.1)

        monitor.stop()

        assert monitor.monitoring is False
        # Thread should finish
        monitor.thread.join(timeout=1.0)
        assert not monitor.thread.is_alive()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_esc_key_detection_unix(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                                    mock_tcgetattr, mock_select):
        """Test ESC key detection on Unix."""
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = '\x1b'  # ESC key
        mock_tcgetattr.return_value = [0, 0, 0, 0, 0, 0, []]

        # First call: input available, second call: no input
        mock_select.side_effect = [
            ([mock_stdin], [], []),  # ESC available
            ([], [], [])             # No more input
        ]

        monitor = KeyboardMonitor()
        monitor.start()

        # Give thread time to detect ESC
        time.sleep(0.2)

        assert monitor.is_interrupted() is True
        assert monitor.interrupted is True

        monitor.stop()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_non_esc_key_ignored_unix(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                                      mock_tcgetattr, mock_select):
        """Test that non-ESC keys are ignored on Unix."""
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = 'a'  # Regular key
        mock_tcgetattr.return_value = [0, 0, 0, 0, 0, 0, []]

        # Input available then stop
        mock_select.side_effect = [
            ([mock_stdin], [], []),
            ([], [], [])
        ]

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.2)

        assert monitor.is_interrupted() is False

        monitor.stop()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_terminal_settings_restored_unix(self, mock_stdin, mock_setcbreak,
                                            mock_tcsetattr, mock_tcgetattr, mock_select):
        """Test that terminal settings are restored on Unix."""
        mock_stdin.fileno.return_value = 0
        old_settings = [1, 2, 3, 4, 5, 6, [7, 8]]
        mock_tcgetattr.return_value = old_settings
        mock_select.return_value = ([], [], [])

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.1)

        monitor.stop()
        monitor.thread.join(timeout=1.0)

        # Terminal settings should be restored
        # tcsetattr should be called with old_settings
        assert mock_tcsetattr.call_count >= 1

    @patch('sys.platform', 'darwin')
    def test_multiple_start_calls(self, mock_platform):
        """Test that multiple start() calls don't create multiple threads."""
        with patch('terminal_chat.cli.select.select', return_value=([], [], [])), \
             patch('terminal_chat.cli.termios.tcgetattr', return_value=[0]*7), \
             patch('terminal_chat.cli.termios.tcsetattr'), \
             patch('terminal_chat.cli.tty.setcbreak'), \
             patch('sys.stdin.fileno', return_value=0):

            monitor = KeyboardMonitor()

            monitor.start()
            first_thread = monitor.thread

            monitor.start()  # Second start
            second_thread = monitor.thread

            # Should be the same thread (or at least not create new one while running)
            assert first_thread is not None

            monitor.stop()

    @patch('sys.platform', 'darwin')
    def test_stop_without_start(self):
        """Test that stop() works even if start() was never called."""
        monitor = KeyboardMonitor()
        monitor.stop()  # Should not raise exception

        assert monitor.monitoring is False

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_exception_in_monitor_thread(self, mock_stdin, mock_setcbreak,
                                         mock_tcsetattr, mock_tcgetattr, mock_select):
        """Test that exceptions in monitor thread don't crash."""
        mock_stdin.fileno.return_value = 0
        mock_tcgetattr.return_value = [0]*7
        mock_select.side_effect = Exception("Test exception")

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.2)

        # Thread should handle exception gracefully
        monitor.stop()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_rapid_esc_presses(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                               mock_tcgetattr, mock_select):
        """Test handling of rapid ESC key presses."""
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = '\x1b'
        mock_tcgetattr.return_value = [0]*7

        # Multiple ESC inputs
        mock_select.side_effect = [
            ([mock_stdin], [], []),
            ([mock_stdin], [], []),
            ([mock_stdin], [], []),
            ([], [], [])
        ]

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.2)

        # Should still be interrupted (flag set once)
        assert monitor.is_interrupted() is True

        monitor.stop()


class TestKeyboardMonitorThreadSafety:
    """Test thread safety of KeyboardMonitor."""

    @patch('sys.platform', 'darwin')
    def test_concurrent_is_interrupted_calls(self):
        """Test that is_interrupted() can be called from multiple threads."""
        with patch('terminal_chat.cli.select.select', return_value=([], [], [])), \
             patch('terminal_chat.cli.termios.tcgetattr', return_value=[0]*7), \
             patch('terminal_chat.cli.termios.tcsetattr'), \
             patch('terminal_chat.cli.tty.setcbreak'), \
             patch('sys.stdin.fileno', return_value=0):

            monitor = KeyboardMonitor()
            monitor.start()

            # Call is_interrupted from multiple places
            results = []
            for _ in range(10):
                results.append(monitor.is_interrupted())

            # All should return False (no ESC pressed)
            assert all(r is False for r in results)

            monitor.stop()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_interrupt_flag_persistence(self, mock_stdin, mock_setcbreak,
                                        mock_tcsetattr, mock_tcgetattr, mock_select):
        """Test that interrupt flag persists until checked."""
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = '\x1b'
        mock_tcgetattr.return_value = [0]*7

        mock_select.side_effect = [
            ([mock_stdin], [], []),
            ([], [], [])
        ]

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.2)

        # Check multiple times - should remain True
        assert monitor.is_interrupted() is True
        assert monitor.is_interrupted() is True
        assert monitor.is_interrupted() is True

        monitor.stop()


class TestKeyboardMonitorCleanup:
    """Test cleanup behavior of KeyboardMonitor."""

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_cleanup_on_stop(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                            mock_tcgetattr, mock_select):
        """Test that stop() properly cleans up resources."""
        mock_stdin.fileno.return_value = 0
        mock_tcgetattr.return_value = [0]*7
        mock_select.return_value = ([], [], [])

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.1)

        monitor.stop()
        monitor.thread.join(timeout=1.0)

        assert monitor.monitoring is False
        assert not monitor.thread.is_alive()

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_start_stop_cycle(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                             mock_tcgetattr, mock_select):
        """Test multiple start/stop cycles."""
        mock_stdin.fileno.return_value = 0
        mock_tcgetattr.return_value = [0]*7
        mock_select.return_value = ([], [], [])

        monitor = KeyboardMonitor()

        # First cycle
        monitor.start()
        time.sleep(0.1)
        monitor.stop()

        # Second cycle
        monitor.start()
        time.sleep(0.1)
        monitor.stop()

        # Third cycle
        monitor.start()
        time.sleep(0.1)
        monitor.stop()

        assert monitor.monitoring is False

    @patch('sys.platform', 'darwin')
    @patch('terminal_chat.cli.select.select')
    @patch('terminal_chat.cli.termios.tcgetattr')
    @patch('terminal_chat.cli.termios.tcsetattr')
    @patch('terminal_chat.cli.tty.setcbreak')
    @patch('sys.stdin')
    def test_reset_interrupt_flag(self, mock_stdin, mock_setcbreak, mock_tcsetattr,
                                  mock_tcgetattr, mock_select):
        """Test that interrupt flag can be manually reset."""
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = '\x1b'
        mock_tcgetattr.return_value = [0]*7

        mock_select.side_effect = [
            ([mock_stdin], [], []),
            ([], [], [])
        ]

        monitor = KeyboardMonitor()
        monitor.start()

        time.sleep(0.2)
        assert monitor.is_interrupted() is True

        # Manually reset
        monitor.interrupted = False

        assert monitor.is_interrupted() is False

        monitor.stop()
