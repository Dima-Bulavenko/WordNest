from django.urls import path

from dictionary import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("translate/", views.TranslationView.as_view(), name="translation")
]
