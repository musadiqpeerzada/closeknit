from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    # auth
    path("signup", views.SignUpView.as_view(), name="signup"),
    path("logout", views.LogoutView.as_view(), name="custom_logout"),
    # communities
    path(
        "communities/list",
        login_required(views.CommunityListView.as_view()),
        name="community_list",
    ),
    path(
        "communities/add",
        login_required(views.CommunityAddView.as_view(extra_context={"view": "add"})),
        name="community_add",
    ),
    path(
        "communities/update/<int:pk>",
        login_required(
            views.CommunityUpdateView.as_view(extra_context={"view": "update"})
        ),
        name="community_update",
    ),
    path(
        "communities/join/<int:pk>",
        login_required(views.CommunityAddMemberView.as_view()),
        name="community_add_member",
    ),
    path(
        "communities/leave/<int:pk>",
        login_required(views.CommunityRemoveMemberView.as_view()),
        name="community_remove_member",
    ),
    path(
        "communities/delete/<int:pk>",
        login_required(
            views.CommunityDeleteView.as_view(extra_context={"view": "delete"})
        ),
        name="community_delete",
    ),
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
        login_required(
            views.SubscriptionAddView.as_view(extra_context={"view": "add"})
        ),
        name="subscription_add",
    ),
    path(
        "subscriptions/update/<int:pk>",
        login_required(
            views.SubscriptionUpdateView.as_view(extra_context={"view": "update"})
        ),
        name="subscription_update",
    ),
    path(
        "subscriptions/delete/<int:pk>",
        login_required(
            views.SubscriptionDeleteView.as_view(extra_context={"view": "delete"})
        ),
        name="subscription_delete",
    ),
]
