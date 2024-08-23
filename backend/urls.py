from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("signup", views.SignUpView.as_view(), name="signup"),
]
