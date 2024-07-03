from pathlib import Path
from unittest.mock import MagicMock, patch

from azure.ai.translation.text.models import TranslatedTextItem
from azure.core.exceptions import HttpResponseError
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from dictionary.forms import LoginForm
from dictionary.models import User
from dictionary.search_manager import TranslationAPI


class UserSetUpMixing:
    def setUp(self):
        self.user_model = get_user_model()
        self.test_email = "testeamil@test.com"
        self.test_pwd = "testpassword"


class UserManagerTest(UserSetUpMixing, TestCase):
    def test_create_user(self):
        user = self.user_model.objects.create_user(email=self.test_email,
                                             password=self.test_pwd)
        user_exist = self.user_model.objects.filter(email=self.test_email).exists()

        self.assertEqual(user.email, self.test_email)
        self.assertTrue(user_exist)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.test_pwd))
    
    def test_create_user_without_email(self):
        message = "Users must have an email address"

        with self.assertRaises(ValueError) as e:
            self.user_model.objects.create_user(email="", password=self.test_pwd)
        self.assertEqual(str(e.exception), message)

    def test_create_superuser(self):
        user = self.user_model.objects.create_superuser(email=self.test_email,
                                             password=self.test_pwd)
        user_exist = self.user_model.objects.filter(email=self.test_email).exists()

        self.assertEqual(user.email, self.test_email)
        self.assertTrue(user_exist)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(self.test_pwd))
    
    def test_invalid_superuser_field(self):
        exp_msg = "Superuser must have is_superuser=True."
        with self.assertRaisesMessage(ValueError, exp_msg):
            self.user_model.objects.create_superuser(self.test_email, self.test_pwd, is_superuser=False)


class UserTest(UserSetUpMixing, TestCase):
    
    def test_model_fields(self):
        is_active = False
        is_superuser = False
        user = self.user_model(email=self.test_email,
                               password=self.test_pwd,
                               is_active=is_active,
                               is_superuser=is_superuser)
        
        self.assertEqual(user.email, self.test_email)
        self.assertEqual(user.password, self.test_pwd)
        self.assertEqual(user.is_active, is_active)
        self.assertEqual(user.is_superuser, is_superuser)
        self.assertTrue(hasattr(user, "date_joined"))
    
    def test_is_staff_property(self):
        user = self.user_model(email=self.test_email,
                               password=self.test_pwd,
                               is_superuser=False)
        
        # Because is_staff property always is equal is_superuser one
        # It should change when is_superuser changes

        self.assertEqual(user.is_staff, user.is_superuser)

        user.is_superuser = True

        self.assertEqual(user.is_staff, user.is_superuser)

    def test_str_method(self):
        user = self.user_model(email=self.test_email,
                               password=self.test_pwd)
        
        self.assertEqual(str(user), user.email)


class LoginFormTest(TestCase):
    def test_form_has_no_password_help_text(self):
        form = LoginForm()

        self.assertIsNone(form.fields["password"].help_text)

    def test_form_has_forgot_pwd_property(self):
        form = LoginForm()

        self.assertIn('forgot_pwd', dir(form))

    def test_forgot_pwd_property_returns_correct_html(self):
        form = LoginForm()
        reset_url = reverse("account_reset_password")
        expected_html = f'<div class="forgot_pwd align-center auth-link"><a href="{reset_url}">Forgot your password?</a></div>'

        self.assertEqual(form.forgot_pwd, expected_html)
    
    @patch('dictionary.forms.reverse')
    def test_forgot_pwd_property_returns_none(self, mock_reverse):
        mock_reverse.side_effect = NoReverseMatch
        form = LoginForm()

        self.assertIsNone(form.forgot_pwd)
    

class IndexViewTest(TestCase):
    def setUp(self):
        self.url = reverse("home")
        self.email = "test@gmail.com"
        self.password = "Testpwd8"
    
    def test_user_authenticated(self):
        User.objects.create_user(email=self.email, password=self.password)
        self.client.login(email=self.email, password=self.password)
        path_to_template = Path("dictionary", "index.html")
        context_title = "WordNest Online Dictionary"
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(path_to_template, response.template_name)
        self.assertEqual(response.context_data["title"], context_title)
    
    def test_user_not_authenticated(self):
        path_to_template = Path("welcome.html")
        context_title = "Welcome"
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(path_to_template, response.template_name)
        self.assertEqual(response.context_data["title"], context_title)


class TranslationAPITest(TestCase):
    def setUp(self):
        self.mock_config = patch("dictionary.search_manager.config").start()
        self.mock_client = patch("dictionary.search_manager.TextTranslationClient").start()
        self.mock_credentials = patch("dictionary.search_manager.AzureKeyCredential").start()
        
        self.addCleanup(patch.stopall)  # Stop all patches after test

        self.mock_config.return_value = "test_key"
        self.mock_credentials.return_value = "test_credentials"

        self.params = {"from_language": "en", "to_language": "es", "body": "Hello"}
    
    def test_init(self):
        
        api = TranslationAPI(**self.params)

        self.assertTrue(hasattr(api, "client"))
        self.assertTrue(api.from_language == self.params["from_language"])
        self.assertTrue(api.to_language == self.params["to_language"])
        self.assertTrue(api.body == self.params["body"])

        self.mock_config.assert_called_once_with("AZURE_TRANSLATOR_KEY")
        self.mock_credentials.assert_called_once_with(self.mock_config.return_value)
        self.mock_client.assert_called_once_with(credential=self.mock_credentials.return_value)
    
    def test_translate_has_dictionary_entries(self):
        test_data = {"test": "dictionary entries"}
        api = TranslationAPI(**self.params)
        mock_lookup_dictionary_entries = patch.object(api, "lookup_dictionary_entries").start()
        mock_translate_text = patch.object(api, "translate_text").start()

        mock_lookup_dictionary_entries.return_value = test_data

        data = api.translate()
        
        self.assertEqual(data, test_data)
        mock_lookup_dictionary_entries.assert_called_once()
        mock_translate_text.assert_not_called()
    
    def test_translate_no_dictionary_entries(self):
        test_data = {"test": "translation"}
        api = TranslationAPI(**self.params)
        mock_lookup_dictionary_entries = patch.object(api, "lookup_dictionary_entries").start()
        mock_translate_text = patch.object(api, "translate_text").start()

        mock_lookup_dictionary_entries.return_value = None
        mock_translate_text.return_value = test_data

        data = api.translate()
        
        self.assertEqual(data, test_data)
        mock_lookup_dictionary_entries.assert_called_once()
        mock_translate_text.assert_called_once()

    def test_translate_text(self):
        not_templated_test_data = [{"test": "not templated data"}]
        templated_test_data = {"test": "templated data"}
        api = TranslationAPI(**self.params)
        mock_get_templated_data = patch.object(api,
                                               "get_templated_data",
                                               return_value=templated_test_data).start()
        api.client.translate.return_value = not_templated_test_data

        data = api.translate_text()
        
        self.assertEqual(data, templated_test_data)
        api.client.translate.assert_called_once_with(body=[api.body],
                                                     from_language=api.from_language,
                                                     to_language=[api.to_language])
        mock_get_templated_data.assert_called_once_with(not_templated_test_data[0])

    def test_lookup_dictionary_entries_no_errors(self):
        not_templated_test_data = [{"test": "not templated data"}]
        templated_test_data = {"test": "templated data"}

        api = TranslationAPI(**self.params)
        api.client.lookup_dictionary_entries.return_value = not_templated_test_data
        mock_get_templated_data = patch.object(api, "get_templated_data").start()
        mock_has_translation = patch.object(api, "has_translation").start()
        mock_get_templated_data.return_value = templated_test_data
        mock_has_translation.return_value = True

        data = api.lookup_dictionary_entries()

        self.assertEqual(data, templated_test_data)
        api.client.lookup_dictionary_entries.assert_called_once_with(body=[api.body],
                                                                     from_language=api.from_language,
                                                                     to_language=api.to_language)
        mock_has_translation.assert_called_once_with(not_templated_test_data[0])
        mock_get_templated_data.assert_called_once_with(not_templated_test_data[0])
    
    def test_lookup_dictionary_entries_with_error_code_400050(self):
        api = TranslationAPI(**self.params)
        patch.object(api, "get_templated_data").start()
        patch.object(api, "has_translation").start()
        mock_exception = HttpResponseError()
        mock_exception.error = MagicMock()
        mock_exception.error.code = 400050
        api.client.lookup_dictionary_entries.side_effect = mock_exception

        data = api.lookup_dictionary_entries()

        self.assertEqual(data, None)
        api.client.lookup_dictionary_entries.assert_called_once_with(body=[api.body],
                                                                     from_language=api.from_language,
                                                                     to_language=api.to_language)
        api.has_translation.assert_not_called()
        api.get_templated_data.assert_not_called()
    
    def test_lookup_dictionary_entries_raise_exception(self):
        api = TranslationAPI(**self.params)
        patch.object(api, "get_templated_data").start()
        patch.object(api, "has_translation").start()
        mock_exception = HttpResponseError()
        mock_exception.error = MagicMock()
        mock_exception.error.code = 4

        api.client.lookup_dictionary_entries.side_effect = mock_exception

        with self.assertRaises(HttpResponseError):
            api.lookup_dictionary_entries()
        
        api.client.lookup_dictionary_entries.assert_called_once_with(body=[api.body],
                                                                     from_language=api.from_language,
                                                                     to_language=api.to_language)
        api.has_translation.assert_not_called()
        api.get_templated_data.assert_not_called()

    def test_get_templated_data_with_text_translated(self):
        translations = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        data = MagicMock(spec=TranslatedTextItem)
        data.translations = translations

        api = TranslationAPI(**self.params)
        result = api.get_templated_data(data)
        translations = result["translations"]
        check_translations = [trans['pos'] == "" and trans["prefix_word"] == "" for trans in translations]

        self.assertEqual(result["form_lang"], api.from_language)
        self.assertEqual(result["to_lang"], api.to_language)
        self.assertEqual(result["word"], api.body)
        self.assertTrue(len(result["translations"]) <= 3)
        self.assertTrue(all(check_translations))
    
    def test_get_templated_data_with_dict_translated(self):
        translations = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        data = MagicMock()
        data.translations = translations

        api = TranslationAPI(**self.params)
        result = api.get_templated_data(data)
        translations = result["translations"]
        check_translations = [isinstance(trans['pos'], MagicMock) and
                              isinstance(trans["prefix_word"], MagicMock) for trans in translations]

        self.assertEqual(result["form_lang"], api.from_language)
        self.assertEqual(result["to_lang"], api.to_language)
        self.assertEqual(result["word"], api.body)
        self.assertTrue(len(result["translations"]) <= 3)
        self.assertTrue(all(check_translations))

    def test_has_translation_with_translations(self):
        data = {"translations": ["test_translation"]}

        api = TranslationAPI(**self.params)
        result = api.has_translation(data)

        self.assertTrue(result)
    
    def test_has_translation_without_translations(self):
        data = {"translations": []}

        api = TranslationAPI(**self.params)
        result = api.has_translation(data)

        self.assertFalse(result)


class TranslationViewTest(TestCase):
    def get_translations(self):
        return {
            "form_lang": self.params["from_language"],
            "to_lang": self.params["to_language"],
            "word": self.params["body"],
            "translations": [
                {"text": "здравствуйте", "pos": "NOUN", "prefix_word": ""},
                {"text": "привіт", "pos": "NOUN", "prefix_word": ""},
                {"text": "здрастуйте", "pos": "NOUN", "prefix_word": ""},
            ],
        }

    def setUp(self):
        self.url = reverse("translation")
        self.params = {"from_language": "en", "to_language": "uk", "body": "Hello"}
        self.headers = {"X-Requested-With": "XMLHttpRequest"}
        self.trans_api = patch("dictionary.views.TranslationAPI").start()
        self.trans_api.return_value.translate.return_value = self.get_translations()
        self.addCleanup(patch.stopall)

    def test_post_request_ajax(self):
        response = self.client.post(
            self.url,
            data=self.params,
            headers=self.headers,
            content_type="application/json",
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.get_translations())
        self.trans_api.assert_called_once_with(**self.params)
        self.trans_api.return_value.translate.assert_called_once()
    
    def test_post_request_not_ajax(self):
        response = self.client.post(
            self.url,
            data=self.params,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
