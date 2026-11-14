"""The list price of `claude-fable-5-2` (2026-11-14): $8 input, $40 output, $0.20 cache read per million tokens."""
import tokens


def test_a_fable_5_2_call_has_a_cost():
    u = {"input_tokens": 1000, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 1_000_000,
         "output_tokens": 10_000}
    assert round(tokens.usd(u, "claude-fable-5-2"), 6) == round((8 * 1000 + 0.20 * 1_000_000 + 40 * 10_000) / 1e6, 6)


def test_the_model_id_with_a_context_suffix_has_the_same_price():
    u = {"input_tokens": 0, "cache_read_input_tokens": 1_000_000, "output_tokens": 0}
    assert round(tokens.usd(u, "claude-fable-5-2[1m]"), 6) == 0.2
