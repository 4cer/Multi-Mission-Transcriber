from pathlib import Path

def make_clickable_path(file_path: str, display_text: str | None = None) -> str:
    """
    Return a string that prints a clickable file link in a terminal
    supporting OSC 8.

    The link always uses the absolute path, so it works even when the
    script is run from different working directories.
    """
    absolute = Path(file_path).resolve()
    uri = absolute.as_uri()
    text = display_text if display_text is not None else file_path
    return f"\x1b]8;;{uri}\x1b\\{text}\x1b]8;;\x1b\\"