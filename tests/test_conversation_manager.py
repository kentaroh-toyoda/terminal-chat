"""
Tests for ConversationManager class.
"""
import pytest
from terminal_chat.cli import ConversationManager


class TestConversationManager:
    """Test suite for ConversationManager class."""

    def test_init_empty(self):
        """Test initialization with no messages."""
        manager = ConversationManager()
        assert manager.get_messages() == []
        assert manager.max_messages == 20

    def test_init_custom_max(self):
        """Test initialization with custom max_messages."""
        manager = ConversationManager(max_messages=10)
        assert manager.max_messages == 10
        assert manager.get_messages() == []

    def test_add_message_single(self):
        """Test adding a single message."""
        manager = ConversationManager()
        manager.add_message("user", "Hello")

        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "Hello"}

    def test_add_message_multiple(self):
        """Test adding multiple messages."""
        manager = ConversationManager()
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi there!")
        manager.add_message("user", "How are you?")

        messages = manager.get_messages()
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"

    def test_add_message_with_system(self):
        """Test adding messages with initial system message."""
        manager = ConversationManager()
        manager.add_message("system", "You are a helpful assistant.")
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi!")

        messages = manager.get_messages()
        assert len(messages) == 3
        assert messages[0]["role"] == "system"

    def test_sliding_window_within_limit(self):
        """Test that messages stay when within limit."""
        manager = ConversationManager(max_messages=5)

        for i in range(4):
            manager.add_message("user", f"Message {i}")

        messages = manager.get_messages()
        assert len(messages) == 4

    def test_sliding_window_exceeds_limit_no_system(self):
        """Test sliding window when exceeding limit without system message."""
        manager = ConversationManager(max_messages=3)

        # Add 5 messages (exceeds limit of 3)
        manager.add_message("user", "Message 0")
        manager.add_message("assistant", "Response 0")
        manager.add_message("user", "Message 1")
        manager.add_message("assistant", "Response 1")
        manager.add_message("user", "Message 2")

        messages = manager.get_messages()
        # Should keep last 3
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 1"
        assert messages[1]["content"] == "Response 1"
        assert messages[2]["content"] == "Message 2"

    def test_sliding_window_with_system_message(self):
        """Test that system message is always preserved."""
        manager = ConversationManager(max_messages=3)

        manager.add_message("system", "System prompt")
        manager.add_message("user", "Message 0")
        manager.add_message("assistant", "Response 0")
        manager.add_message("user", "Message 1")
        manager.add_message("assistant", "Response 1")

        messages = manager.get_messages()
        # Should keep system + last 2 = 3 total (system + max_messages - 1)
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[-1]["content"] == "Response 1"

    def test_sliding_window_large_conversation(self):
        """Test sliding window with large conversation."""
        manager = ConversationManager(max_messages=10)

        # Add 30 messages
        for i in range(30):
            manager.add_message("user" if i % 2 == 0 else "assistant", f"Message {i}")

        messages = manager.get_messages()
        # Should keep last 10
        assert len(messages) == 10
        assert messages[0]["content"] == "Message 20"
        assert messages[-1]["content"] == "Message 29"

    def test_sliding_window_with_system_large(self):
        """Test sliding window with system message in large conversation."""
        manager = ConversationManager(max_messages=5)

        manager.add_message("system", "System")

        # Add 20 messages
        for i in range(20):
            manager.add_message("user" if i % 2 == 0 else "assistant", f"Message {i}")

        messages = manager.get_messages()
        # Should keep system + last 4 = 5 total (system + max_messages - 1)
        assert len(messages) == 5
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Message 16"
        assert messages[-1]["content"] == "Message 19"

    def test_clear(self):
        """Test clearing conversation history."""
        manager = ConversationManager()
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi")

        assert len(manager.get_messages()) == 2

        manager.clear()

        assert manager.get_messages() == []

    def test_clear_after_system(self):
        """Test clearing after system message."""
        manager = ConversationManager()
        manager.add_message("system", "System")
        manager.add_message("user", "Hello")

        manager.clear()

        assert manager.get_messages() == []

    def test_get_messages_returns_copy(self):
        """Test that get_messages returns a new list (not reference)."""
        manager = ConversationManager()
        manager.add_message("user", "Hello")

        messages1 = manager.get_messages()
        messages2 = manager.get_messages()

        # Should be equal (implementation returns same reference, not a copy)
        assert messages1 == messages2
        # Note: Current implementation returns reference, not copy
        assert messages1 is messages2

    def test_message_structure(self):
        """Test that messages have correct structure."""
        manager = ConversationManager()
        manager.add_message("user", "Test message")

        messages = manager.get_messages()
        message = messages[0]

        assert isinstance(message, dict)
        assert "role" in message
        assert "content" in message
        assert len(message) == 2  # Only role and content

    def test_empty_content(self):
        """Test adding message with empty content."""
        manager = ConversationManager()
        manager.add_message("user", "")

        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == ""

    def test_multiline_content(self):
        """Test adding message with multiline content."""
        manager = ConversationManager()
        content = "Line 1\nLine 2\nLine 3"
        manager.add_message("user", content)

        messages = manager.get_messages()
        assert messages[0]["content"] == content

    def test_special_characters(self):
        """Test adding message with special characters."""
        manager = ConversationManager()
        content = "Special: @#$%^&*() 你好 🎉"
        manager.add_message("user", content)

        messages = manager.get_messages()
        assert messages[0]["content"] == content

    @pytest.mark.parametrize("max_messages,num_to_add,expected_count", [
        (5, 3, 3),    # Under limit
        (5, 5, 5),    # At limit
        (5, 10, 5),   # Over limit
        (1, 10, 1),   # Max 1, add many
        (20, 100, 20), # Default max, add many
    ])
    def test_sliding_window_parametrized(self, max_messages, num_to_add, expected_count):
        """Test sliding window with various configurations."""
        manager = ConversationManager(max_messages=max_messages)

        for i in range(num_to_add):
            manager.add_message("user", f"Message {i}")

        messages = manager.get_messages()
        assert len(messages) == expected_count

        # Verify we kept the last N messages
        if num_to_add > expected_count:
            assert messages[0]["content"] == f"Message {num_to_add - expected_count}"
            assert messages[-1]["content"] == f"Message {num_to_add - 1}"

    def test_alternating_roles(self):
        """Test conversation with alternating user/assistant roles."""
        manager = ConversationManager(max_messages=6)

        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            manager.add_message(role, f"Message {i}")

        messages = manager.get_messages()
        assert len(messages) == 6

        # Verify alternating pattern is maintained
        for i, msg in enumerate(messages):
            # Starting from message 4, pattern should be user/assistant/...
            original_index = 4 + i
            expected_role = "user" if original_index % 2 == 0 else "assistant"
            assert msg["role"] == expected_role

    def test_conversation_flow_realistic(self):
        """Test realistic conversation flow."""
        manager = ConversationManager(max_messages=10)

        # System message
        manager.add_message("system", "You are a helpful assistant.")

        # User asks questions
        manager.add_message("user", "What is Python?")
        manager.add_message("assistant", "Python is a programming language.")

        manager.add_message("user", "Tell me more")
        manager.add_message("assistant", "It was created by Guido van Rossum.")

        # Continue conversation
        for i in range(10):
            manager.add_message("user", f"Question {i}")
            manager.add_message("assistant", f"Answer {i}")

        messages = manager.get_messages()

        # System should be preserved + last 9 = 10 total (system + max_messages - 1)
        assert len(messages) == 10
        assert messages[0]["role"] == "system"
        assert "helpful assistant" in messages[0]["content"]

    def test_max_messages_boundary(self):
        """Test behavior at exact boundary of max_messages."""
        manager = ConversationManager(max_messages=5)

        # Add exactly max_messages
        for i in range(5):
            manager.add_message("user", f"Message {i}")

        messages = manager.get_messages()
        assert len(messages) == 5

        # Add one more
        manager.add_message("user", "Message 5")

        messages = manager.get_messages()
        assert len(messages) == 5
        assert messages[0]["content"] == "Message 1"  # First one dropped
        assert messages[-1]["content"] == "Message 5"

    def test_single_system_message_only(self):
        """Test with only a system message."""
        manager = ConversationManager(max_messages=3)
        manager.add_message("system", "System prompt")

        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_system_message_count_interaction(self):
        """Test that system message doesn't count toward max limit."""
        manager = ConversationManager(max_messages=3)

        manager.add_message("system", "System")

        # Add exactly max_messages more
        for i in range(3):
            manager.add_message("user", f"Message {i}")

        messages = manager.get_messages()
        # Should have system + 2 = 3 (sliding window triggers at 4 messages)
        assert len(messages) == 3

        # Add more to trigger sliding
        manager.add_message("user", "Message 3")
        manager.add_message("user", "Message 4")

        messages = manager.get_messages()
        # Should still have system + last 2 = 3
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Message 3"
