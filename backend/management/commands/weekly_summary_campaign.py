import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from backend.services import (
    get_subscriptions_available_for_share,
    get_items_available_for_lease,
)


def format_email_content(shared_items, shared_subscriptions):
    content = "Here's what's new in your Closeknit communities this week:\n\n"

    if shared_items:
        content += "Shared Items:\n"
        for item in shared_items:
            content += f"- {item.name} (shared by {item.owner.username})\n"
        content += "\n"

    if shared_subscriptions:
        content += "Shared Subscriptions:\n"
        for subscription in shared_subscriptions:
            content += (
                f"- {subscription.name} (shared by {subscription.owner.username})\n"
            )

    content += "\nVisit Closeknit to learn more about these shared resources & Always feel free to reach out to your closeknit community!"
    return content


class Command(BaseCommand):
    help = "Send weekly email to users about items and subscriptions shared with them"

    def handle(self, *args, **options):
        seven_days_ago = timezone.now() - timedelta(days=7)
        users = User.objects.all()

        for user in users:
            # Fetch items shared with the user in the last 7 days
            shared_items = get_items_available_for_lease(user).filter(
                created_at__gte=seven_days_ago
            )

            # Fetch subscriptions shared with the user in the last 7 days
            shared_subscriptions = get_subscriptions_available_for_share(user).filter(
                created_at__gte=seven_days_ago
            )

            if shared_items or shared_subscriptions:
                self.send_email(user, shared_items, shared_subscriptions)

    def send_email(self, user, shared_items, shared_subscriptions):
        subject = "Your community is sharing! 🎉"
        message = format_email_content(shared_items, shared_subscriptions)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        print(
            json.dumps(
                dict(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                ),
                indent=4,
            )
        )
        # send_mail(subject, message, from_email, recipient_list)
        self.stdout.write(self.style.SUCCESS(f"Email sent to {user.email}"))
