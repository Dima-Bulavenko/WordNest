from typing import Union

from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import DictionaryLookupItem, TranslatedTextItem
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from decouple import config
from django.db.models import QuerySet

from dictionary.models import Translation


class TranslationAPI:
    def __init__(self, *, from_language: str, to_language: str, body: str):
        self.__key = AzureKeyCredential(config("AZURE_TRANSLATOR_KEY"))
        self.client = TextTranslationClient(credential=self.__key)
        self.from_language = from_language
        self.to_language = to_language
        self.body = body

    def translate(self) -> dict:
        """
        Translates text by looking up dictionary entries and translating text.

        This method first attempts to translate the text by looking up dictionary entries.
        If no dictionary entries are found, it falls back to translating the text.

        Returns:
            dict: The translated text as a dictionary.
        """
        if db_translations := self.get_db_translation():
            return db_translations
        
        if dictionary_translations := self.lookup_dictionary_entries():
            return dictionary_translations

        return self.translate_text()

    def translate_text(self) -> dict:
        """
        Translates text using a client service.

        Send a request to the client service to translate the text from 
        the source language to the target language.

        Returns:
            dict: The translated text as a dictionary.
        """
        data = self.client.translate(
            body=[self.body],
            from_language=self.from_language,
            to_language=[self.to_language],
        )[0]

        return self.get_templated_data(data)

    def lookup_dictionary_entries(self) -> DictionaryLookupItem:
        """
        Looks up dictionary entries for the text.

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
    
