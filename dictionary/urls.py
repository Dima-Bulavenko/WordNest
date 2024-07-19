from django.urls import path

from dictionary import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("translate/", views.TranslationView.as_view(), name="translation"),
    path("dictionary/<str:source>-<str:target>", views.DictionaryView.as_view(), name="dictionary"),
    path("dictionary/create", views.CreateDictionaryView.as_view(), name="create_dictionary"),
    path("dictionary/delete/<int:pk>", views.DeleteDictionaryView.as_view(), name="delete_dictionary"),
    path("dictionary/add-word/", views.AddWordView.as_view(), name="add_word_to_dictionary"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("account/delete/", views.DeleteAccountView.as_view(), name="delete_account"),
]
