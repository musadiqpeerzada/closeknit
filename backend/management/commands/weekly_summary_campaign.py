import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMessage

from backend.services import (
    get_requests_for_user,
    get_subscriptions_available_for_share,
    get_items_available_for_lease,
)


def format_email_content(shared_items, shared_subscriptions, shared_requests):
    closeknit_link = '<a href="https://closeknit.io">Closeknit</a>'
    content = f" We're thrilled to share some exciting updates from your {closeknit_link} community!<br><br>"

    if shared_items:
        content += "<h2>📢 What's in the Sharing Pool:</h2>"
        for item in shared_items:
            content += f"- {item.name} (shared by {item.owner.username})<br>"

    if shared_subscriptions:
        content += "<h2>📢 Subscriptions available for sharing</h2>:"
        for subscription in shared_subscriptions:
            content += (
                f"- {subscription.name} (shared by {subscription.owner.username})<br>"
            )

    if shared_requests:
        content += "<h2>📢 Items and Subscriptions Requested by Your Community:</h2>"
        for request in shared_requests:
            content += f"- {request.name} (shared by {request.owner.username})<br>"

    content += """
<br><br>Remember, sharing is caring! Feel free to reach out to members of your community if you'd like to borrow these items. It's a great way to connect with your neighbors and make the most of our shared resources.

<br><br>Have something interesting to share with the community? We'd love to see what you can add to our growing pool of shared treasures at <a href="https://closeknit.io">Closeknit</a>!

<br><br>Curious to learn more? Visit our <a href="https://closeknit.io">Closeknit</a> website to discover all the amazing resources available in your community.

<br><br>Stay connected, stay sharing, and enjoy the power of community!    
    """
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

            shared_requests = get_requests_for_user(user)

            if shared_items or shared_subscriptions or shared_requests:
                self.send_email(user, shared_items, shared_subscriptions, shared_requests)

    def send_email(self, user, shared_items, shared_subscriptions, shared_requests):
        subject = "Exciting Updates from Your Closeknit Community! 🎉"
        message = format_email_content(shared_items, shared_subscriptions, shared_requests)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        print(
            json.dumps(
                dict(
                    subject=subject,
                    message=message,
                    from_email=f"Closeknit <{from_email}>",
                    recipient_list=recipient_list,
                ),
                indent=4,
            )
        )
        email_message = EmailMessage(
            subject=subject,
            body=message,
            from_email=f"Closeknit <{from_email}>",
            to=recipient_list,
        )
        email_message.content_subtype = "html"  # Main content is now text/html
        email_message.send()
        self.stdout.write(self.style.SUCCESS(f"Email sent to {recipient_list}"))
