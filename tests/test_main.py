from health_checker.utils import get_event_bridge_schedule


def test_main() -> None:
    assert get_event_bridge_schedule()
