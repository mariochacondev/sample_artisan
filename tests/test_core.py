import pytest

from sample_artisan import craft_sample


def test_craft_sample_normalizes_text() -> None:
    assert craft_sample("  hello   world  ") == "sample_artisan crafted: hello world"


def test_craft_sample_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="text must not be empty"):
        craft_sample("   ")
