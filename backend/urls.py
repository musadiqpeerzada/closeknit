from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("about", views.about_view, name="about"),
    # auth
    path("signup", views.SignUpView.as_view(), name="signup"),
    path("logout", views.LogoutView.as_view(), name="custom_logout"),
    path("profile", views.profile_view, name="profile"),
    # communities
    path(
        "communities/<int:pk>",
        views.community_detail_view,
        name="community_detail",
    ),
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
        "subscriptions/discover",
        login_required(views.DiscoverListView.as_view()),
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
    # items
    path(
        "items/list",
        login_required(views.ItemsListView.as_view()),
        name="item_list",
    ),
    path(
        "items/add",
        login_required(views.ItemCreateView.as_view(extra_context={"view": "add"})),
        name="item_add",
    ),
    path(
        "items/update/<int:pk>",
        login_required(views.ItemUpdateView.as_view(extra_context={"view": "update"})),
        name="item_update",
    ),
    path(
        "items/delete/<int:pk>",
        login_required(views.ItemDeleteView.as_view(extra_context={"view": "delete"})),
        name="item_delete",
    ),
    # leases
    path(
        "leases/add",
        login_required(views.LeaseCreateView.as_view(extra_context={"view": "add"})),
        name="lease_add",
    ),
    path(
        "leases/update/<int:pk>",
        login_required(views.LeaseUpdateView.as_view(extra_context={"view": "update"})),
        name="lease_update",
    ),
    path(
        "leases/delete/<int:pk>",
        login_required(views.LeaseDeleteView.as_view(extra_context={"view": "delete"})),
        name="lease_delete",
    ),
    #     invite endpoints
    path("community/<int:community_id>/invite/", views.send_invite, name="send_invite"),
    path("invite/<uuid:token>/", views.accept_invite, name="accept_invite"),
]
