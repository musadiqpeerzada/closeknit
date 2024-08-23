from django.db import models


class Subscription(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        "auth.User", related_name="subscriptions", on_delete=models.CASCADE
    )
    shared_to = models.ManyToManyField(
        "auth.User", related_name="shared_subscriptions", blank=True
    )

    def __str__(self):
        return self.name


class Community(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        "auth.User", related_name="communities", on_delete=models.CASCADE
    )
    members = models.ManyToManyField(
        "auth.User", related_name="community_members", blank=True
    )

    def __str__(self):
        return self.name
