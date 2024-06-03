from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from dictionary.forms import LoginForm


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
