from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import CreateView

from backend.models import Subscription, Community


class RegistrationForm(UserCreationForm):
    usable_password = None


class SignUpView(CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class IndexView(generic.TemplateView):
    template_name = "backend/index.html"


class SubscriptionListView(generic.ListView):
    template_name = "backend/subscription/list.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return Subscription.objects.filter(owner=self.request.user)


class SharedSubscriptionListView(generic.ListView):
    template_name = "backend/subscription/shared.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return Subscription.objects.filter(shared_to=self.request.user)


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
    template_name = "backend/subscription/add.html"
    model = Subscription
    fields = ["name", "is_active", "shared_to"]
    success_url = reverse_lazy("subscription_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class SubscriptionUpdateView(generic.UpdateView):
    template_name = "backend/subscription/update.html"
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
    template_name = "backend/subscription/delete.html"
    model = Subscription
    success_url = reverse_lazy("subscription_list")

    def get_queryset(self):
        return Subscription.objects.filter(owner=self.request.user)
