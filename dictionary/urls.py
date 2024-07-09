from django.urls import path

from dictionary import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("translate/", views.TranslationView.as_view(), name="translation"),
    path("dictionary/create", views.CreateDictionaryView.as_view(), name="create_dictionary")
]
