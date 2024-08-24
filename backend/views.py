from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import CreateView

from backend.models import Subscription, Community


def get_user(user_name: str):
    try:
        return User.objects.get(username=user_name)
    except User.DoesNotExist:
        return None


class RegistrationForm(UserCreationForm):
    usable_password = None


class SignUpView(CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class LogoutView(generic.TemplateView):
    template_name = "registration/logout.html"


class IndexView(generic.TemplateView):
    template_name = "backend/index.html"


class SubscriptionListView(generic.ListView):
    template_name = "backend/subscription/list.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return dict(
            owned=Subscription.objects.filter(owner=self.request.user),
            shared=Subscription.objects.filter(shared_to=self.request.user),
        )


class DiscoverSubscriptionListView(generic.ListView):
    template_name = "backend/subscription/discover.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        # TODO: horrible query, but it works. fix it later
        communities_the_user_belongs_to = Community.objects.filter(
            members=self.request.user
        )
        all_users_of_communities_the_user_belongs_to = [
            user
            for community in communities_the_user_belongs_to
            for user in community.members.all()
        ]
        all_subscriptions_of_users_in_communities_the_user_belongs_to = (
            Subscription.objects.filter(
                owner__in=all_users_of_communities_the_user_belongs_to
            )
        )
        return all_subscriptions_of_users_in_communities_the_user_belongs_to.exclude(
            owner=self.request.user
        ).exclude(shared_to=self.request.user)


class SubscriptionAddView(generic.CreateView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    fields = ["name", "is_active", "shared_to"]
    success_url = reverse_lazy("subscription_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class SubscriptionUpdateView(generic.UpdateView):
    template_name = "backend/subscription/cud.html"
    model = Subscription
    fields = ["name", "is_active", "shared_to"]
    success_url = reverse_lazy("subscription_list")

    def get_queryset(self):
        return Subscription.objects.filter(owner=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields["shared_to"].queryset = form.fields["shared_to"].queryset.exclude(
            id=self.request.user.id
        )

        return form


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
        return Community.objects.filter(owner=self.request.user)


class CommunityUpdateView(generic.UpdateView):
    template_name = "backend/community/cud.html"
    model = Community
    fields = ["name", "is_active"]
    success_url = reverse_lazy("community_list")

    def get_queryset(self):
        return Community.objects.filter(owner=self.request.user)


class UpdateCommunityMembersForm(forms.Form):
    user_name = forms.CharField(label="username", max_length=100)


class CommunityAddMemberView(generic.FormView):
    template_name = "backend/community/add_member.html"
    form_class = UpdateCommunityMembersForm
    success_url = reverse_lazy("community_list")

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


class RemoveCommunityMembersForm(forms.Form):
    user_name = forms.CharField(label="username", max_length=100)


class CommunityRemoveMemberView(generic.FormView):
    template_name = "backend/community/remove_member.html"
    form_class = RemoveCommunityMembersForm
    success_url = reverse_lazy("community_list")

    def form_valid(self, form):
        user_name = form.cleaned_data["user_name"]
        community_id = self.kwargs["pk"]
        user_with_user_name: User | None = get_user(user_name=user_name)
        if user_with_user_name.username == self.request.user.username:
            form.add_error(
                "user_name", "you cannot remove yourself from your community my friend"
            )
            return super().form_invalid(form)
        if user_with_user_name is None:
            form.add_error("user_name", "User not found")
            return super().form_invalid(form)

        community = Community.objects.get(pk=community_id)
        if community.members.filter(username=user_with_user_name.username).exists():
            community.members.remove(user_with_user_name)
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
