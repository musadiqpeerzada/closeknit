import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.utils import timezone
from django.dispatch import receiver


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
    shared_with = models.ManyToManyField(
        "Community", related_name="shared_subscriptions", blank=True
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
    invite_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    BOOK = "book"
    ELECTRONICS = "electronics"
    OTHER = "other"
    ITEM_TYPE_CHOICES = [
        (BOOK, "Book"),
        (ELECTRONICS, "Electronics"),
        (OTHER, "Other"),
    ]

    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default=OTHER,
    )
    shared_with = models.ManyToManyField(
        Community, related_name="shared_items", blank=True
    )

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


@receiver(pre_save, sender=Lease)
def pre_save_lease(sender, instance, **kwargs):
    instance.clean()


class Request(models.Model):
    ITEM = "item"
    SUBSCRIPTION = "subscription"
    REQUEST_TYPE_CHOICES = [
        (ITEM, "Item"),
        (SUBSCRIPTION, "Subscription"),
    ]

    name = models.CharField(max_length=100)
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default=ITEM,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    shared_with = models.ManyToManyField(
        Community, related_name="shared_requests", blank=True
    )

    def __str__(self):
        return self.name
