from datetime import datetime

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.generic import CreateView

from backend.models import Subscription, Community, Item, Lease, Invite


def get_user(user_name: str):
    try:
        return User.objects.get(username=user_name)
    except User.DoesNotExist:
        return None


def get_all_users_from_communities_the_user_belongs_to(user: User) -> list[User]:
    assert isinstance(user, User)

    # TODO: horrible query, but it works. fix it later
    communities_the_user_belongs_to = Community.objects.filter(members=user)
    all_users_of_communities_the_user_belongs_to = [
        user
        for community in communities_the_user_belongs_to
        for user in community.members.all()
    ]
    return all_users_of_communities_the_user_belongs_to


def get_items_available_for_lease(user: User) -> QuerySet[Item]:
    all_users_of_communities_the_user_belongs_to = (
        get_all_users_from_communities_the_user_belongs_to(user)
    )
    all_items_of_users_in_communities_the_user_belongs_to = Item.objects.filter(
        owner__in=all_users_of_communities_the_user_belongs_to, is_active=True
    )
    items_already_leased_out = Lease.objects.filter(
        end_date__gt=datetime.now(),
        item__in=all_items_of_users_in_communities_the_user_belongs_to,
    )

    return all_items_of_users_in_communities_the_user_belongs_to.exclude(
        owner=user
    ).exclude(pk__in=[lease.item.pk for lease in items_already_leased_out])


def get_subscriptions_available_for_share(user: User) -> QuerySet[Subscription]:
    all_users_of_communities_the_user_belongs_to = (
        get_all_users_from_communities_the_user_belongs_to(user)
    )
    all_subscriptions_of_users_in_communities_the_user_belongs_to = (
        Subscription.objects.filter(
            owner__in=all_users_of_communities_the_user_belongs_to
        )
    )
    return all_subscriptions_of_users_in_communities_the_user_belongs_to.exclude(
        owner=user
    ).exclude(shared_to=user)


class RegistrationForm(UserCreationForm):
    usable_password = None


class SignUpView(CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class LogoutView(generic.TemplateView):
    template_name = "registration/logout.html"


def index_view(request):
    if not request.user.is_authenticated:
        return render(request, "backend/index.html")

    users_in_communities = get_all_users_from_communities_the_user_belongs_to(
        request.user
    )
    your_items_count = Item.objects.filter(owner=request.user).count()
    your_subscriptions_count = Subscription.objects.filter(owner=request.user).count()
    items_available_for_lease = get_items_available_for_lease(request.user).count()
    subscriptions_available_for_share = get_subscriptions_available_for_share(
        user=request.user
    ).count()
    total_active_members_across_communities = len(users_in_communities)
    total_communities_user_belongs_to = len(
        Community.objects.filter(members=request.user)
    )
    dashboard_data = dict(
        your_items_count=your_items_count,
        your_subscriptions_count=your_subscriptions_count,
        total_shared_items=your_items_count + your_subscriptions_count,
        items_available_for_lease=items_available_for_lease,
        subscriptions_available_for_share=subscriptions_available_for_share,
        total_available_items=items_available_for_lease
        + subscriptions_available_for_share,
        total_communities_user_belongs_to=total_communities_user_belongs_to,
        total_active_members_across_communities=total_active_members_across_communities,
    )
    return render(request, "backend/index.html", dashboard_data)


class IndexView(generic.TemplateView):
    template_name = "backend/index.html"

    def get_context_data(self):
        users_in_communities = get_all_users_from_communities_the_user_belongs_to(
            self.request.user
        )
        your_items_count = Item.objects.filter(owner=self.request.user).count()
        your_subscriptions_count = Subscription.objects.filter(
            owner=self.request.user
        ).count()
        items_available_for_lease = get_items_available_for_lease(
            self.request.user
        ).count()
        subscriptions_available_for_share = get_subscriptions_available_for_share(
            user=self.request.user
        ).count()
        total_active_members_across_communities = len(users_in_communities)
        return dict(
            your_items_count=your_items_count,
            your_subscriptions_count=your_subscriptions_count,
            items_available_for_lease=items_available_for_lease,
            subscriptions_available_for_share=subscriptions_available_for_share,
            total_active_members_across_communities=total_active_members_across_communities,
        )


class SubscriptionListView(generic.ListView):
    template_name = "backend/subscription/list.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return dict(
            owned=Subscription.objects.filter(owner=self.request.user),
            shared=Subscription.objects.filter(shared_to=self.request.user),
        )


class DiscoverListView(generic.ListView):
    template_name = "backend/discover.html"
    context_object_name = "discover"

    def get_subscriptions_to_discover(self):
        all_users_of_communities_the_user_belongs_to = (
            get_all_users_from_communities_the_user_belongs_to(self.request.user)
        )
        all_subscriptions_of_users_in_communities_the_user_belongs_to = (
            Subscription.objects.filter(
                owner__in=all_users_of_communities_the_user_belongs_to
            )
        )
        return all_subscriptions_of_users_in_communities_the_user_belongs_to.exclude(
            owner=self.request.user
        ).exclude(shared_to=self.request.user)

    def get_items_to_discover(self):
        all_users_of_communities_the_user_belongs_to = (
            get_all_users_from_communities_the_user_belongs_to(self.request.user)
        )
        all_items_of_users_in_communities_the_user_belongs_to = Item.objects.filter(
            owner__in=all_users_of_communities_the_user_belongs_to, is_active=True
        )
        items_already_leased_out = Lease.objects.filter(
            end_date__gt=datetime.now(),
            item__in=all_items_of_users_in_communities_the_user_belongs_to,
        )

        return all_items_of_users_in_communities_the_user_belongs_to.exclude(
            owner=self.request.user
        ).exclude(pk__in=[lease.item.pk for lease in items_already_leased_out])

    def get_queryset(self):
        all_users_of_communities_the_user_belongs_to = (
            get_all_users_from_communities_the_user_belongs_to(self.request.user)
        )
        all_subscriptions_of_users_in_communities_the_user_belongs_to = (
            Subscription.objects.filter(
                owner__in=all_users_of_communities_the_user_belongs_to
            )
        )
        subscriptions_to_discover = (
            all_subscriptions_of_users_in_communities_the_user_belongs_to.exclude(
                owner=self.request.user
            ).exclude(shared_to=self.request.user)
        )
        items_to_discover = self.get_items_to_discover()
        return dict(subscriptions=subscriptions_to_discover, items=items_to_discover)


class SubscriptionAddForm(forms.ModelForm):
    shared_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Subscription
        fields = ["name", "is_active", "shared_to"]


class SubscriptionAddView(generic.CreateView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    form_class = SubscriptionAddForm
    success_url = reverse_lazy("subscription_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.owner = self.request.user

        form.fields["shared_to"].queryset = User.objects.filter(
            pk__in=[
                user.pk
                for user in get_all_users_from_communities_the_user_belongs_to(
                    self.request.user
                )
            ]
        ).exclude(pk=self.request.user.pk)
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class SubscriptionUpdateForm(forms.ModelForm):
    shared_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Subscription
        fields = ["name", "is_active", "shared_to"]


class SubscriptionUpdateView(generic.UpdateView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    form_class = SubscriptionUpdateForm
    success_url = reverse_lazy("subscription_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["shared_to"].queryset = User.objects.filter(
            pk__in=[
                user.pk
                for user in get_all_users_from_communities_the_user_belongs_to(
                    self.request.user
                )
            ]
        ).exclude(pk=self.request.user.pk)
        return form

    def get_queryset(self):
        return Subscription.objects.filter(owner=self.request.user)


class SubscriptionDeleteView(generic.DeleteView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    success_url = reverse_lazy("subscription_list")

    def get_queryset(self):
        return Subscription.objects.filter(owner=self.request.user)


class CommunityListView(generic.ListView):
    template_name = "backend/community/list.html"
    context_object_name = "communities"

    def get_queryset(self):
        return dict(
            owned=Community.objects.filter(owner=self.request.user),
            shared=Community.objects.filter(members=self.request.user),
        )


class CommunityUpdateForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "is_active", "members"]


class CommunityUpdateView(generic.UpdateView):
    template_name = "backend/community/cud.html"
    model = Community
    form_class = CommunityUpdateForm
    success_url = reverse_lazy("community_list")

    def get_queryset(self):
        return Community.objects.filter(owner=self.request.user)


class UpdateCommunityMembersForm(forms.Form):
    user_name = forms.CharField(label="username", max_length=100)


class CommunityAddMemberView(generic.FormView):
    template_name = "backend/community/add_member.html"
    form_class = UpdateCommunityMembersForm
    success_url = reverse_lazy("community_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["community"] = Community.objects.get(pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        user_name = form.cleaned_data["user_name"]
        community_id = self.kwargs["pk"]
        user_with_mobile_number: User | None = get_user(user_name=user_name)
        if user_with_mobile_number is None:
            form.add_error("user_name", "User not found")
            return super().form_invalid(form)

        community = Community.objects.get(pk=community_id)
        if not community.members.filter(
            username=user_with_mobile_number.username
        ).exists():
            community.members.add(user_with_mobile_number)
            community.save()
        return super().form_valid(form)


class CommunityAddView(generic.CreateView):
    template_name = "backend/community/cud.html"
    model = Community
    fields = ["name"]
    success_url = reverse_lazy("community_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        community = form.save()
        community.members.add(self.request.user)
        return super().form_valid(form)


class CommunityDeleteView(generic.DeleteView):
    template_name = "backend/community/cud.html"
    model = Community
    success_url = reverse_lazy("community_list")

    def get_queryset(self):
        return Community.objects.filter(owner=self.request.user)


class ItemsListView(generic.ListView):
    template_name = "backend/item/list.html"
    context_object_name = "items"

    def get_queryset(self):
        return dict(
            owned=Item.objects.filter(owner=self.request.user),
            leased=Lease.objects.filter(lessee=self.request.user),
            leased_out=Lease.objects.filter(item__owner=self.request.user),
        )


class ItemCreateView(generic.CreateView):
    template_name = "backend/item/cud.html"
    model = Item
    fields = ["name"]
    success_url = reverse_lazy("item_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ItemUpdateView(generic.UpdateView):
    template_name = "backend/item/cud.html"
    model = Item
    fields = ["name", "is_active"]
    success_url = reverse_lazy("item_list")

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user)


class ItemDeleteView(generic.DeleteView):
    template_name = "backend/item/cud.html"
    model = Item
    success_url = reverse_lazy("item_list")

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user)


class LeaseBaseView(generic.View):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["item"].queryset = Item.objects.filter(
            owner=self.request.user
        ).exclude(is_active=False)

        form.fields["lessee"].queryset = User.objects.filter(
            pk__in=[
                user.pk
                for user in get_all_users_from_communities_the_user_belongs_to(
                    self.request.user
                )
            ]
        ).exclude(pk=self.request.user.pk)

        form.fields["lessee"].label = "Borrower"
        form.fields["start_date"].widget = forms.widgets.DateTimeInput(
            attrs={"type": "datetime-local"}
        )
        form.fields["end_date"].widget = forms.widgets.DateTimeInput(
            attrs={"type": "datetime-local"}
        )

        return form


class LeaseCreateView(LeaseBaseView, generic.CreateView):
    template_name = "backend/lease/cud.html"
    model = Lease
    fields = ["item", "lessee", "start_date", "end_date"]
    success_url = reverse_lazy("item_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class LeaseUpdateView(LeaseBaseView, generic.UpdateView):
    template_name = "backend/lease/cud.html"
    model = Lease
    fields = ["item", "lessee", "start_date", "end_date"]
    success_url = reverse_lazy("item_list")


class LeaseDeleteView(generic.DeleteView):
    template_name = "backend/lease/cud.html"
    model = Lease
    success_url = reverse_lazy("item_list")

    def get_queryset(self):
        return Lease.objects.filter(item__owner=self.request.user)


@login_required
def send_invite(request, community_id):
    community = get_object_or_404(Community, id=community_id, owner=request.user)
    if request.method == "POST":
        invite = Invite.objects.create(community=community, created_by=request.user)
        invite_url = request.build_absolute_uri(
            reverse("accept_invite", args=[str(invite.token)])
        )
        return render(
            request,
            "backend/invite/show_invite_link.html",
            {"invite_url": invite_url, "community": community},
        )
    return render(request, "backend/invite/send_invite.html", {"community": community})


def accept_invite(request, token):
    invite = get_object_or_404(Invite, token=token)
    if invite.is_used or invite.is_expired():
        return HttpResponseBadRequest("This invite is no longer valid.")

    if request.user.is_authenticated:
        if request.method == "POST":
            if invite.use_invite(request.user):
                invite.community.members.add(request.user)
                return redirect("community_list")
            else:
                return HttpResponseBadRequest("Unable to use this invite.")
        return render(request, "backend/invite/confirm_invite.html", {"invite": invite})
    else:
        # TODO: get google account log using reverse or something along those lines
        return redirect(
            f"/accounts/google/login/?process=login&next={reverse('accept_invite', args=[token])}"
        )
