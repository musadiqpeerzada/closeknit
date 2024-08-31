import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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


class Item(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} (owned by {self.owner.username})"

    def is_leased(self):
        # Returns True if the item is currently leased
        current_lease = (
            Lease.objects.filter(item=self)
            .filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())
            .exists()
        )
        return current_lease


class Lease(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    lessee = models.ForeignKey(
        "auth.User", related_name="leases", on_delete=models.CASCADE
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def clean(self):
        # Ensure that there is no overlap in leases for the same item
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

        overlapping_leases = Lease.objects.filter(
            item=self.item, start_date__lt=self.end_date, end_date__gt=self.start_date
        ).exclude(pk=self.id)

        if overlapping_leases.exists():
            raise ValidationError(
                "This item is already leased during the given period."
            )

    def __str__(self):
        return f"Lease of {self.item.name} by {self.lessee.username} from {self.start_date} to {self.end_date}"


class Invite(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_invites",
    )
    used_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_invites",
    )
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invite from {self.created_by.username} to {self.community.name}"

    def is_expired(self):
        return (timezone.now() - self.created_at).days >= 1

    def use_invite(self, user):
        if not self.is_used and not self.is_expired():
            self.is_used = True
            self.used_by = user
            self.used_at = timezone.now()
            self.save()
            return True
        return False
