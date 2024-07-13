def normalize_string(string: str) -> str:
    """
    Normalize a string by removing leading and trailing whitespace and converting it to lowercase.
    """
    if not isinstance(string, str):
        raise TypeError(f"Expected a string, but got {type(string)}")
    
    return string.strip().lower()
