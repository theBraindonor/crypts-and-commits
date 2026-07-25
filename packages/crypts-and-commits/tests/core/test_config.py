from cac.core import config


def test_summary_key_is_defined() -> None:
    assert config.SUMMARY_KEY == "summary"


def test_summary_max_length_is_500() -> None:
    assert config.SUMMARY_MAX_LENGTH == 500
