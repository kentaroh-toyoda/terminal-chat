"""
Tests for CostTracker class.
"""
import pytest
from terminal_chat.cli import CostTracker


class TestCostTracker:
    """Test suite for CostTracker class."""

    def test_init_empty(self):
        """Test initialization with no usage."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0

    def test_add_usage_basic(self):
        """Test adding token usage."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(10, 20)

        assert tracker.total_input_tokens == 10
        assert tracker.total_output_tokens == 20

    def test_add_usage_multiple(self):
        """Test adding multiple usage entries."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(10, 20)
        tracker.add_usage(5, 15)
        tracker.add_usage(3, 7)

        assert tracker.total_input_tokens == 18
        assert tracker.total_output_tokens == 42

    def test_add_usage_zero(self):
        """Test adding zero token usage."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(0, 0)

        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0

    def test_get_cost_claude_haiku(self):
        """Test cost calculation for Claude Haiku 4.5."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(1_000_000, 2_000_000)  # 1M input, 2M output

        cost = tracker.get_cost()
        assert cost is not None
        # $1 per 1M input + $5 per 1M output * 2 = $11
        assert cost["input_cost"] == 1.0
        assert cost["output_cost"] == 10.0
        assert cost["total_cost"] == 11.0

    def test_get_cost_gpt_5_mini(self):
        """Test cost calculation for GPT-5 Mini."""
        tracker = CostTracker("openai/gpt-5-mini")
        tracker.add_usage(1_000_000, 4_000_000)  # 1M input, 4M output

        cost = tracker.get_cost()
        assert cost is not None
        # $0.25 per 1M input + $2 per 1M output * 4 = $8.25
        assert cost["input_cost"] == 0.25
        assert cost["output_cost"] == 8.0
        assert cost["total_cost"] == 8.25

    def test_get_cost_gemini_flash(self):
        """Test cost calculation for Gemini 2.5 Flash."""
        tracker = CostTracker("google/gemini-2.5-flash")
        tracker.add_usage(1_000_000, 1_000_000)  # 1M each

        cost = tracker.get_cost("google/gemini-2.5-flash")
        assert cost is not None
        # $0.30 per 1M input + $2.50 per 1M output = $2.80
        assert cost["input_cost"] == 0.30
        assert cost["output_cost"] == 2.50
        assert cost["total_cost"] == 2.80

    def test_get_cost_unknown_model(self):
        """Test cost calculation for unknown model returns None."""
        tracker = CostTracker("unknown/model")
        tracker.add_usage(100, 200)

        cost = tracker.get_cost()
        assert cost is None

    def test_get_cost_partial_tokens(self):
        """Test cost calculation with partial token counts."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(500_000, 250_000)  # Half million

        cost = tracker.get_cost()
        assert cost is not None
        # $1 per 1M * 0.5 + $5 per 1M * 0.25 = $1.75
        assert cost["input_cost"] == 0.5
        assert cost["output_cost"] == 1.25
        assert cost["total_cost"] == 1.75

    def test_get_cost_small_tokens(self):
        """Test cost calculation with small token counts."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(100, 500)  # Small amounts

        cost = tracker.get_cost()
        assert cost is not None
        # Very small costs
        expected_input = 100 / 1_000_000 * 0.25
        expected_output = 500 / 1_000_000 * 2.0
        assert abs(cost[0] - expected_input) < 0.0001
        assert abs(cost[1] - expected_output) < 0.0001
        assert abs(cost[2] - (expected_input + expected_output)) < 0.0001

    def test_format_cost_with_pricing(self):
        """Test formatting cost display when pricing is available."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(1000, 5000)

        formatted = tracker.format_cost("anthropic/claude-haiku-4.5")
        assert "Tokens: 1000 in / 5000 out" in formatted
        assert "Cost:" in formatted
        assert "$" in formatted

    def test_format_cost_without_pricing(self):
        """Test formatting cost display when pricing is not available."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(1000, 5000)

        formatted = tracker.format_cost()
        assert "Tokens: 1000 in / 5000 out" in formatted
        assert "Cost:" not in formatted

    def test_format_cost_zero_tokens(self):
        """Test formatting with zero tokens."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")

        formatted = tracker.format_cost("anthropic/claude-haiku-4.5")
        assert "Tokens: 0 in / 0 out" in formatted

    def test_cost_calculation_precision(self):
        """Test that cost calculations maintain precision."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(123_456, 789_012)

        cost = tracker.get_cost()
        assert cost is not None

        # Verify precision to 4 decimal places
        expected_input = 123_456 / 1_000_000 * 1.0
        expected_output = 789_012 / 1_000_000 * 5.0

        assert abs(cost[0] - expected_input) < 0.0001
        assert abs(cost[1] - expected_output) < 0.0001

    def test_multiple_models_in_sequence(self):
        """Test getting costs for different models with same tracker."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(1_000_000, 1_000_000)

        cost_claude = tracker.get_cost("anthropic/claude-haiku-4.5")
        cost_gpt = tracker.get_cost()
        cost_gemini = tracker.get_cost("google/gemini-2.5-flash")

        # All should use same token counts but different pricing
        assert cost_claude[2] == 6.0  # 1 + 5
        assert cost_gpt[2] == 2.25  # 0.25 + 2
        assert cost_gemini[2] == 2.80  # 0.30 + 2.50

    @pytest.mark.parametrize("input_tokens,output_tokens", [
        (0, 0),
        (1, 1),
        (100, 100),
        (1000, 1000),
        (10_000, 10_000),
        (100_000, 100_000),
        (1_000_000, 1_000_000),
    ])
    def test_various_token_amounts(self, input_tokens, output_tokens):
        """Test cost calculation with various token amounts."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(input_tokens, output_tokens)

        assert tracker.total_input_tokens == input_tokens
        assert tracker.total_output_tokens == output_tokens

        cost = tracker.get_cost()
        if input_tokens > 0 or output_tokens > 0:
            assert cost is not None
            assert cost[0] >= 0  # input cost
            assert cost[1] >= 0  # output cost
            assert cost[2] >= 0  # total cost
            assert cost[2] == cost[0] + cost[1]

    @pytest.mark.parametrize("model_name", [
        "anthropic/claude-haiku-4.5",
        "openai/gpt-5-mini",
        "google/gemini-2.5-flash",
    ])
    def test_all_supported_models(self, model_name):
        """Test that all supported models return valid costs."""
        tracker = CostTracker("anthropic/claude-haiku-4.5")
        tracker.add_usage(1_000_000, 1_000_000)

        cost = tracker.get_cost(model_name)
        assert cost is not None
        assert len(cost) == 3
        assert all(isinstance(c, float) for c in cost)
        assert all(c >= 0 for c in cost)
