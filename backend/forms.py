from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from backend.models import Community, Subscription, Item, Request


class RegistrationForm(UserCreationForm):
    usable_password = None


class SubscriptionAddForm(forms.ModelForm):
    shared_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Subscription
        fields = ["name", "is_active", "shared_to", "shared_with"]


class SubscriptionUpdateForm(forms.ModelForm):
    shared_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Subscription
        fields = ["name", "is_active", "shared_to", "shared_with"]


class CommunityUpdateForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "is_active", "members"]


class UpdateCommunityMembersForm(forms.Form):
    user_name = forms.CharField(label="username", max_length=100)


class ItemCreateForm(forms.ModelForm):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Item
        fields = ["name", "item_type", "shared_with"]


class ItemUpdateForm(forms.ModelForm):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Item
        fields = ["name", "is_active", "item_type", "shared_with"]


class RequestCreateForm(forms.ModelForm):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=Community.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Request
        fields = ["name", "request_type", "shared_with"]
