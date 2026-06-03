"""Core behavior for the sample_artisan starter project."""


def craft_sample(text: str) -> str:
    """Return a normalized sample phrase.

    Args:
        text: Input text to normalize.

    Raises:
        ValueError: If the input is empty or only whitespace.
    """
    normalized = " ".join(text.strip().split())
    if not normalized:
        raise ValueError("text must not be empty")

    return f"sample_artisan crafted: {normalized}"
