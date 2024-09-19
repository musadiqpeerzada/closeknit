from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.urls import reverse
from datetime import datetime

from backend.models import Subscription, Community, Item, Lease


def get_user(user_name: str) -> User | None:
    try:
        return User.objects.get(username=user_name)
    except User.DoesNotExist:
        return None


def get_all_users_from_communities_the_user_belongs_to(user: User) -> list[User]:
    communities_the_user_belongs_to = Community.objects.filter(members=user)
    return list(
        User.objects.filter(community_members__in=communities_the_user_belongs_to)
        .exclude(id=user.id)
        .distinct()
    )


def get_items_available_for_lease(user: User) -> QuerySet[Item]:
    communities_the_user_belongs_to = Community.objects.filter(members=user)
    items_shared_to_communities_the_user_belongs_to = Item.objects.filter(
        shared_with__in=communities_the_user_belongs_to
    )
    items_already_leased_out = Lease.objects.filter(
        end_date__gt=datetime.now(),
        item__in=items_shared_to_communities_the_user_belongs_to,
    )
    return items_shared_to_communities_the_user_belongs_to.exclude(owner=user).exclude(
        pk__in=[lease.item.pk for lease in items_already_leased_out]
    )


def get_subscriptions_available_for_share(user: User) -> QuerySet[Subscription]:
    communities_the_user_belongs_to = Community.objects.filter(members=user)
    subscriptions_shared_to_communities_the_user_belongs_to = (
        Subscription.objects.filter(shared_with__in=communities_the_user_belongs_to)
    )
    return subscriptions_shared_to_communities_the_user_belongs_to.exclude(owner=user)


def get_dashboard_data(user: User) -> dict:
    items_available_for_lease = get_items_available_for_lease(user)
    subscriptions_available_for_share = get_subscriptions_available_for_share(user=user)

    return {
        "items_available_for_lease": items_available_for_lease,
        "subscriptions_available_for_share": subscriptions_available_for_share,
    }


def get_user_subscriptions(user: User) -> dict:
    return {
        "owned": Subscription.objects.filter(owner=user),
        "shared": Subscription.objects.filter(shared_to=user),
        "discover": get_subscriptions_available_for_share(user),
    }


def get_user_communities(user: User) -> dict:
    return {
        "owned": Community.objects.filter(owner=user),
        "shared": Community.objects.filter(members=user),
    }


def get_user_items(user: User) -> dict:
    return {
        "owned": Item.objects.filter(owner=user),
        "leased": Lease.objects.filter(lessee=user),
        "leased_out": Lease.objects.filter(item__owner=user),
        "discover": get_items_available_for_lease(user),
    }


def add_user_to_community(community: Community, user: User) -> None:
    if not community.members.filter(username=user.username).exists():
        community.members.add(user)
        community.save()


def use_invite(invite_uuid: str, user: User) -> bool:
    community: Community = Community.objects.filter(invite_uuid=invite_uuid).first()
    if not community:
        return False
    community.members.add(user)
    return True


def get_data_for_profile_view(user: User):
    user_name = user.username
    user_profile_picture = SocialAccount.objects.get(user=user).get_avatar_url()
    user_email = user.email
    communities_the_user_is_part_of = Community.objects.filter(members=user)
    items_of_user = Item.objects.filter(owner=user)
    subscriptions_of_user = Subscription.objects.filter(owner=user)
    return dict(
        user_name=user_name,
        user_profile_picture=user_profile_picture,
        user_email=user_email,
        communities_the_user_is_part_of=communities_the_user_is_part_of,
        items_of_user_count=items_of_user.count(),
        subscriptions_of_user_count=subscriptions_of_user.count(),
    )


def __get_invite_link(request, invite_uuid: str) -> str:
    return request.build_absolute_uri(reverse("accept_invite", args=[str(invite_uuid)]))


def get_data_for_community_detail(community_id: int, request) -> dict | None:
    try:
        community = Community.objects.get(id=community_id)
    except Community.DoesNotExist:
        return None

    members = community.members.all()

    shared_items = community.shared_items.all()
    shared_items_count = shared_items.count()
    shared_subscriptions = community.shared_subscriptions.all()
    shared_subscriptions_count = shared_subscriptions.count()
    invite_link = __get_invite_link(request, community.invite_uuid)

    return {
        "pk": community.pk,
        "community_owner": community.owner,
        "community_name": community.name,
        "invite_link": invite_link,
        "created_by": community.owner.username,
        "member_count": members.count(),
        "shared_items": shared_items,
        "shared_items_count": shared_items_count,
        "shared_subscriptions": shared_subscriptions,
        "shared_subscriptions_count": shared_subscriptions_count,
        "members": [
            {
                "username": member.username,
                "email": member.email,
                "profile_picture": (
                    member.socialaccount_set.first().get_avatar_url()
                    if member.socialaccount_set.exists()
                    else None
                ),
            }
            for member in members
        ],
    }
