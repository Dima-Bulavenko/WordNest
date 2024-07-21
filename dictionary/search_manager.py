from __future__ import annotations

from abc import ABC, abstractmethod

from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import DictionaryTranslation, TranslationText
from azure.core.credentials import AzureKeyCredential
from decouple import config
from django.db import transaction
from django.db.models import QuerySet

from dictionary.models import Language, Translation, User, Word


class TranslationStrategy(ABC):
    """
    An abstract class for translation strategies.
    """

    @abstractmethod
    def query_translation(self, word, from_lang, to_lang, user):
        """
        An abstract method to get translations for the word from the source language to the target language.
        """
        pass

    @abstractmethod
    def create_templated_translations(
        self, word, from_lang, to_lang, translations, user
    ):
        """
        An abstract method to create a list of templated translations.
        """
        pass

    def translate(
        self, word: str, from_lang: str, to_lang: str, user: User
    ) -> list[dict]:
        """
        Runs the query_translation() and create_templated_translations() methods to get translations for the word.

        Args:
            word (str): a word to translate
            from_lang (str): the language code of the word
            to_lang (str): the language code to translate the word to
            user (User): the user requesting the translation

        Returns:
            list[dict]: a list of templated translations
        """
        translations = self.query_translation(word, from_lang, to_lang)
        return self.create_templated_translations(
            word, from_lang, to_lang, translations, user
        )

    def get_translation_template(self) -> dict:
        """
        Common template for translation data.
        Returns:
            dict: _description_
        """
        return {
            "text": "",
            "pos": "",
            "prefix_word": "",
            "user_translation": False,
            "translation_type": "",
        }


class DatabaseTranslation(TranslationStrategy):
    def query_translation(self, word, from_lang, to_lang) -> QuerySet:
        return Translation.get_approved_translations(word, from_lang, to_lang)

    def create_templated_translations(
        self, word, from_lang, to_lang, translations, user
    ) -> list:
        dictionary_translations = user.get_word_translations(word, from_lang, to_lang)
        translations = list(translations) + [
            trans for trans in dictionary_translations if trans not in translations
        ]
        templated_translations = []
        for translation in translations:
            template = self.get_translation_template()
            template["text"] = translation.to_word.word
            template["translation_type"] = "database"
            if translation in dictionary_translations:
                template["user_translation"] = True
            templated_translations.append(template)
        return templated_translations


class BaseAzureAPITranslation(TranslationStrategy):
    def __init__(self):
        self.__key = AzureKeyCredential(config("AZURE_TRANSLATOR_KEY"))
        self.client = TextTranslationClient(credential=self.__key)


class DictionaryAPITranslation(BaseAzureAPITranslation):
    def query_translation(
        self, word, from_lang, to_lang
    ) -> list[DictionaryTranslation]:
        if len(word) > 100:
            return []

        translations = self.client.lookup_dictionary_entries(
            body=[word],
            from_language=from_lang,
            to_language=to_lang,
        )[0].translations

        return translations

    def create_templated_translations(
        self, word, from_lang, to_lang, translations, user
    ) -> list:
        templated_translations = []

        for translation in translations:
            template = self.get_translation_template()
            template["text"] = translation.normalized_target
            template["pos"] = translation.pos_tag
            template["prefix_word"] = translation.prefix_word
            template["translation_type"] = "dictionary_api"
            templated_translations.append(template)
        if templated_translations:
            self.__create_approved_translations(
                word, from_lang, to_lang, templated_translations
            )
        return templated_translations

    @staticmethod
    def __create_approved_translations(
        word: str, source_lang_code: str, target_lang_code: str, translations: list
    ) -> None:
        """
        Create approved translations.

        The translations is approved if it was translated by dictionary translation class.

        Args:
            word (str): The word to translate.
            source_lang_code (str): The language code of the language the word is in.
            target_lang_code (str): The language code of the language to translate the word to.
            translations (list): A list of dictionaries, each containing a translation of the word.
                                  Each dictionary must have a "text" key associated with the translated word.
        """
        with transaction.atomic():
            source_lang = Language.objects.get(code=source_lang_code)
            target_lang = Language.objects.get(code=target_lang_code)
            from_word = Word.objects.get_or_create(
                word=word.lower(), language=source_lang
            )[0]
            for translation in translations:
                to_word = Word.objects.get_or_create(
                    word=translation["text"], language=target_lang
                )[0]
                Translation.objects.get_or_create(
                    from_word=from_word, to_word=to_word, defaults={"is_approved": True}
                )


class TextAPITranslation(BaseAzureAPITranslation):
    def query_translation(self, word, from_lang, to_lang) -> list[TranslationText]:
        if len(word) > 1500:
            return []

        return self.client.translate(
            body=[word],
            from_language=from_lang,
            to_language=[to_lang],
        )[0].translations

    def create_templated_translations(
        self, word, from_lang, to_lang, translations, user
    ) -> list:
        templated_translations = []

        for translation in translations:
            template = self.get_translation_template()
            template["text"] = translation.text
            template["translation_type"] = "text_api"
            templated_translations.append(template)

        return templated_translations


class Translator:
    def __init__(self, strategies: list[TranslationStrategy]):
        self._strategies = strategies

    def translate(self, word: str, from_lang: str, to_lang: str, user: User) -> dict:
        templated_data = {
            "form_lang": from_lang,
            "to_lang": to_lang,
            "word": word,
            "translations": [],
        }
        for strategy in self._strategies:
            translations = strategy.translate(word, from_lang, to_lang, user)
            if translations:
                templated_data["translations"] = translations
                break
        return templated_data


def translate(word: str, from_lang: str, to_lang: str, user: User) -> dict:
    strategies = [
        DatabaseTranslation(),
        DictionaryAPITranslation(),
        TextAPITranslation(),
    ]
    translator = Translator(strategies)
    return translator.translate(word, from_lang, to_lang, user)
