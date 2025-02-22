from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.generic import CreateView

from backend.forms import (
    RegistrationForm,
    SubscriptionAddForm,
    SubscriptionUpdateForm,
    CommunityUpdateForm,
    UpdateCommunityMembersForm,
    ItemCreateForm,
    ItemUpdateForm,
    RequestCreateForm,
)
from backend.models import Subscription, Community, Item, Lease, Request
from backend.services import (
    get_user,
    get_all_users_from_communities_the_user_belongs_to,
    get_dashboard_data,
    get_user_subscriptions,
    get_user_communities,
    get_user_items,
    add_user_to_community,
    use_invite,
    get_data_for_profile_view,
    get_data_for_community_detail,
    get_items_available_for_lease,
    get_subscriptions_available_for_share,
    get_requests_for_user,
)


class SignUpView(CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class LogoutView(generic.TemplateView):
    template_name = "registration/logout.html"


def index_view(request):
    if not request.user.is_authenticated:
        return render(request, "backend/index.html")

    dashboard_data = get_dashboard_data(request.user)
    dashboard_data["requests"] = Request.objects.filter(owner=request.user)
    return render(request, "backend/index.html", dashboard_data)


def about_view(request):
    return render(request, "backend/about.html")


@login_required
def profile_view(request):
    return render(
        request, "backend/profile.html", context=get_data_for_profile_view(request.user)
    )


def get_subscription_list_view(request):
    return render(
        request,
        "backend/subscription/list.html",
        context=get_user_subscriptions(request.user),
    )


class SubscriptionListView(generic.ListView):
    template_name = "backend/subscription/list.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return get_user_subscriptions(self.request.user)


def subscription_detail_view(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if (
        subscription.owner != request.user
        and subscription not in get_subscriptions_available_for_share(request.user)
    ):
        return HttpResponseBadRequest("You do not have access to this subscription")
    return render(
        request, "backend/subscription/detail.html", {"subscription": subscription}
    )


class SubscriptionBaseView(generic.View):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["shared_with"].queryset = Community.objects.filter(
            members=self.request.user
        )
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


class SubscriptionAddView(SubscriptionBaseView, generic.CreateView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    form_class = SubscriptionAddForm
    success_url = reverse_lazy("subscription_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class SubscriptionUpdateView(SubscriptionBaseView, generic.UpdateView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    form_class = SubscriptionUpdateForm
    success_url = reverse_lazy("subscription_list")

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
        return get_user_communities(self.request.user)


@login_required
def community_detail_view(request, pk):
    does_user_belong_to_community = Community.objects.filter(
        pk=pk, members=request.user
    ).exists()
    if not does_user_belong_to_community:
        return HttpResponseBadRequest("You do not belong to this community")

    return render(
        request,
        "backend/community/detail.html",
        get_data_for_community_detail(pk, request=request),
    )


class CommunityUpdateView(generic.UpdateView):
    template_name = "backend/community/cud.html"
    model = Community
    form_class = CommunityUpdateForm
    success_url = reverse_lazy("community_list")

    def get_queryset(self):
        return Community.objects.filter(owner=self.request.user)


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
        user_to_add = get_user(user_name=user_name)
        if user_to_add is None:
            form.add_error("user_name", "User not found")
            return super().form_invalid(form)

        community = Community.objects.get(pk=community_id)
        add_user_to_community(community, user_to_add)
        return super().form_valid(form)


class CommunityAddView(generic.CreateView):
    template_name = "backend/community/cud.html"
    model = Community
    fields = ["name"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        community = form.save()
        community.members.add(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("community_detail", kwargs={"pk": self.object.pk})


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
        return get_user_items(self.request.user)


@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user and item not in get_items_available_for_lease(
        request.user
    ):
        return HttpResponseBadRequest("You do not have access to this item")
    return render(request, "backend/item/detail.html", {"item": item})


class ItemBaseView(generic.View):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["shared_with"].queryset = Community.objects.filter(
            members=self.request.user
        )
        return form


class ItemCreateView(ItemBaseView, generic.CreateView):
    template_name = "backend/item/cud.html"
    model = Item
    form_class = ItemCreateForm
    success_url = reverse_lazy("item_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ItemUpdateView(ItemBaseView, generic.UpdateView):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    template_name = "backend/item/cud.html"
    model = Item
    form_class = ItemUpdateForm
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


class RequestBaseView(generic.View):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["shared_with"].queryset = Community.objects.filter(
            members=self.request.user
        )
        return form

class RequestCreateView(RequestBaseView, generic.CreateView):
    template_name = "backend/request/cud.html"
    model = Request
    form_class = RequestCreateForm
    success_url = reverse_lazy("request_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RequestUpdateView(RequestBaseView , generic.UpdateView):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    template_name = "backend/request/cud.html"
    model = Request
    form_class = RequestCreateForm
    success_url = reverse_lazy("request_list")

    def get_queryset(self):
        return Request.objects.filter(owner=self.request.user)


class RequestDeleteView(generic.DeleteView):
    template_name = "backend/request/cud.html"
    model = Request
    success_url = reverse_lazy("request_list")

    def get_queryset(self):
        return Request.objects.filter(owner=self.request.user)


@login_required
def request_detail_view(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if request_obj.owner != request.user and request_obj not in get_requests_for_user(request.user):
        return HttpResponseBadRequest("You do not have access to this request")
    return render(request, "backend/request/detail.html", {"request": request_obj})


class RequestListView(generic.ListView):
    template_name = "backend/request/list.html"
    context_object_name = "requests"

    def get_queryset(self):
        return {
            "discover": get_requests_for_user(self.request.user),
            "owned": Request.objects.filter(owner=self.request.user),
        }


def accept_invite(request, token):
    if request.user.is_authenticated:
        if request.method == "POST":
            is_invite_used, community = use_invite(invite_uuid=token, user=request.user)
            if is_invite_used:
                return redirect("community_detail", community.pk)
            else:
                return HttpResponseBadRequest("Unable to use this invite.")

        community = get_object_or_404(Community, invite_uuid=token)
        return render(
            request, "backend/invite/confirm_invite.html", {"community": community}
        )
    else:
        return redirect(
            f"/accounts/google/login/?process=login&next={reverse('accept_invite', args=[token])}"
        )
