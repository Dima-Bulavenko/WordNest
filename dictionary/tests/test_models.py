from django.db.utils import IntegrityError
from django.test import TestCase

from dictionary.models import Dictionary, Language, Translation, User, Word


class WordTest(TestCase):
    def setUp(self):
        self.language = Language.objects.create(code="en", name="English")
    
    def test_create_word(self):
        word = Word.objects.create(word="hello", language=self.language)

        self.assertEqual(word.word, "hello")
        self.assertEqual(word.language, self.language)
    
    def test_unique_word_language_constraint(self):
        word_text = 'hello'
        Word.objects.create(word=word_text, language=self.language)
        
        with self.assertRaises(IntegrityError):
            Word.objects.create(word=word_text, language=self.language)
        
    def test_str_method(self):
        word = Word.objects.create(word="hello", language=self.language)
        self.assertEqual(str(word), "hello")
    

class LanguageTest(TestCase):
    def test_create_language(self):
        language = Language.objects.create(code="en", name="English")
        
        self.assertEqual(language.code, "en")
        self.assertEqual(language.name, "English")
    
    def test_unique_code_constraint(self):
        code = 'en'
        Language.objects.create(code=code, name="English")
        
        with self.assertRaises(IntegrityError):
            Language.objects.create(code=code, name="Ukrainian")
    
    def test_unique_name_constraint(self):
        name = 'English'
        Language.objects.create(code="en", name=name)
        
        with self.assertRaises(IntegrityError):
            Language.objects.create(code="uk", name=name)
    
    def test_str_method(self):
        name = "English"
        language = Language.objects.create(code="en", name=name)
        self.assertEqual(str(language), name)
