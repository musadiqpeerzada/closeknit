from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    # signup
    path("signup", views.SignUpView.as_view(), name="signup"),
    # subscriptions
    path(
        "subscriptions/list",
        login_required(views.SubscriptionListView.as_view()),
        name="subscription_list",
    ),
    path(
        "subscriptions/shared",
        login_required(views.SharedSubscriptionListView.as_view()),
        name="subscription_shared",
    ),
    path(
        "subscriptions/discover",
        login_required(views.DiscoverSubscriptionListView.as_view()),
        name="subscription_discover",
    ),
    path(
        "subscriptions/add",
        login_required(views.SubscriptionAddView.as_view()),
        name="subscription_add",
    ),
    path(
        "subscriptions/update/<int:pk>",
        login_required(views.SubscriptionUpdateView.as_view()),
        name="subscription_update",
    ),
    path(
        "subscriptions/delete/<int:pk>",
        login_required(views.SubscriptionDeleteView.as_view()),
        name="subscription_delete",
    ),
]
