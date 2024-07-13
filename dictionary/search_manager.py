from __future__ import annotations

from abc import ABC, abstractmethod

from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import DictionaryTranslation, TranslationText
from azure.core.credentials import AzureKeyCredential
from decouple import config
from django.db.models import QuerySet

from dictionary.models import Translation, User


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

    def translate(self, word: str, from_lang: str, to_lang: str, user: User) -> list[dict]:
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

        if dictionary_translations := self.lookup_dictionary_entries():
            self.add_translation_to_db(dictionary_translations)
            return dictionary_translations

class DatabaseTranslation(TranslationStrategy):
    def query_translation(self, word, from_lang, to_lang) -> QuerySet:
        return Translation.get_translations(word, from_lang, to_lang)

    def create_templated_translations(
        self, word, from_lang, to_lang, translations, user
    ) -> list:
        user_dictionary = user.dictionaries.get(
            source_language__code=from_lang, target_language__code=to_lang
        )
        dictionary_translations = user_dictionary.translations.filter(
            from_word__word=word
        )

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


        Send a request to the client service to look up dictionary entries
        for the text from the source language to the target language.

        Returns:
            DictionaryLookupItem: The dictionary entries for the text as a DictionaryLookupItem.
        """
        try:
            data = self.client.lookup_dictionary_entries(
                body=[self.body],
                from_language=self.from_language,
                to_language=self.to_language,
            )[0]
        except HttpResponseError as ex:
            if ex.error.code == 400050:  # text exceeds the maximum length of 100
                return None
            raise

        if self.has_translation(data):
            templated_data = self.get_templated_data(data)
            return templated_data
        return None

    def get_templated_data(
        self, data: Union[DictionaryLookupItem, TranslatedTextItem, QuerySet]
    ) -> dict:
        """
        Formats the translation data into a specific template.

        Takes in a data object, which can be either a DictionaryLookupItem or a
        TranslatedTextItem, and formats the translation data into a specific template.

        Parameters:
            data (Union[DictionaryLookupItem, TranslatedTextItem]): The data object containing
            the translation information.

        Returns:
            dict: A dictionary containing the formatted translation data.
        """
        templated_data = {
            "form_lang": self.from_language,
            "to_lang": self.to_language,
            "word": self.body,
            "translations": [],
        }

        if isinstance(data, QuerySet):
            for translation in data:
                translation_data = {
                    "text": translation.to_word.word,
                    "pos": "",
                    "prefix_word": "",
                }
                templated_data["translations"].append(translation_data)
            return templated_data

        for trans_num, translation in enumerate(data.translations, 1):
            if trans_num > 3:
                break

            if isinstance(data, TranslatedTextItem):
                text = translation.text
                pos = ""
                prefix_word = ""
            else:
                text = translation.normalized_target
                pos = translation.pos_tag
                prefix_word = translation.prefix_word

            translation_data = {
                "text": text,
                "pos": pos,
                "prefix_word": prefix_word,
            }
            templated_data["translations"].append(translation_data)
        return templated_data

    def has_translation(self, data: dict) -> bool:
        """
        Checks if the provided data contains any translations.

        Parameters:
            data (dict): The data object containing the translation information.

        Returns:
            bool: True if the 'translations' key is present and has a truthy value, False otherwise.
        """
        key = "translations"
        return key in data and bool(data[key])
    
    def get_db_translation(self) -> QuerySet:
        """
        Looks up dictionary entries for the text in the database.

        Send a request to the database to look up dictionary entries
        for the text from the source language to the target language.
        """
        data = Translation.get_translations(self.body, self.from_language, self.to_language)
        templated_data = self.get_templated_data(data)
        
        if self.has_translation(templated_data):
            return templated_data
        return None
    
    def add_translation_to_db(self, data: dict):
        """
        Adds the translation to the database.

        Parameters:
            data (dict): The data object containing the translation information.
        """
        source_code = data["form_lang"]
        target_code = data["to_lang"]
        word = data["word"]
        translations = data["translations"]

        Translation.create_translations(word, source_code, target_code, translations)