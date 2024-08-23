from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import CreateView

from backend.models import Subscription


class RegistrationForm(UserCreationForm):
    usable_password = None


class SignUpView(CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class IndexView(generic.ListView):
    template_name = "backend/index.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return Subscription.objects.all()
