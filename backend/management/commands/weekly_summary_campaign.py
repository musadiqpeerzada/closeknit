import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail

from backend.services import (
    get_subscriptions_available_for_share,
    get_items_available_for_lease,
)


def format_email_content(shared_items, shared_subscriptions):
    closeknit_link = '<a href="https://closeknit.io">Closeknit</a>'
    content = (
        f"Here's what's being shared in your {closeknit_link} communities:<br><br>"
    )

    if shared_items:
        content += "Shared Items:<br>"
        for item in shared_items:
            content += f"- {item.name} (shared by {item.owner.username})<br>"
        content += "<br>"

    if shared_subscriptions:
        content += "Shared Subscriptions:<br>"
        for subscription in shared_subscriptions:
            content += (
                f"- {subscription.name} (shared by {subscription.owner.username})<br>"
            )

    content += '<br>Always feel free to reach out to the owners in your closeknit community if you want to borrow. Visit <a href="https://closeknit.io">Closeknit</a> to learn more about these shared resources!'
    return content


class Command(BaseCommand):
    help = "Send weekly email to users about items and subscriptions shared with them"

    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            # Fetch items shared with the user in the last 7 days
            shared_items = get_items_available_for_lease(user)

            # Fetch subscriptions shared with the user in the last 7 days
            shared_subscriptions = get_subscriptions_available_for_share(user)

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
        send_mail(
            subject=subject,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=message,
            message="",
        )
        self.stdout.write(self.style.SUCCESS(f"Email sent to {recipient_list}"))
