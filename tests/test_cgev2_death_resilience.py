from scripts.verify_cgev2_death_resilience import validate_packet


def test_cgev2_death_resilience_packet_is_fail_closed_and_recoverable():
    assert validate_packet() == []
