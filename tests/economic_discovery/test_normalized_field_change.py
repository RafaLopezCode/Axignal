"""Economic state changes require a comparable normalized basis, never empty-set equality."""

import pytest

from application.economic_discovery.observation_memory import normalized_field_change


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (None, (("service", "repair"),), None),
        ((), (), None),
        ((), (("service", "repair"),), None),
        ((("service", "repair"),), (), None),
        ((("service", "repair"),), (("service", "repair"),), False),
        ((("service", "repair"),), (("service", "installation"),), True),
    ],
)
def test_normalized_comparison_remains_tristate(previous, current, expected):
    assert normalized_field_change(previous, current) is expected
