from __future__ import annotations

from dictionary.models import Translation, Word


def normalize_string(string: str) -> str:
    """
    Normalize a string by removing leading and trailing whitespace and converting it to lowercase.
    """
    if not isinstance(string, str):
        raise TypeError(f"Expected a string, but got {type(string)}")

    return string.strip().lower()


def group_translations_by_from_word(
    queryset: iter[Translation],
) -> list[tuple[Word, list[Word]]]:
    """
     Groups translations by their source words.

    This function iterates over an iterable of Translation objects and groups them by the source word (from_word).
    It returns  A list of tuples where first item is the source word (from_word) and the second one the values are
    lists of corresponding target words (to_word).

    Args:
        queryset (iter[Translation]): An iterable of Translation objects to be grouped.

    Returns:
        list[tuple[Word, list[Word]]]: A list of tuples where each tuple contain two elements, the first one is
        a source word (from_word) and an the second is the corresponding value is a list of target words
        (to_word) associated with that source word.
    """
    groped_translations = {}
    for translation in queryset:
        if translation.from_word not in groped_translations:
            groped_translations[translation.from_word] = [translation.to_word]
        else:
            groped_translations[translation.from_word].append(translation.to_word)
    return list(groped_translations.items())
