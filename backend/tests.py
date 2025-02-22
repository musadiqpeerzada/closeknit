from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.test import Client

from backend.models import Community, Item, Subscription, Lease, ItemRequest, SubscriptionRequest
from backend.services import (
    get_items_available_for_lease,
    get_subscriptions_available_for_share,
)


class CommunityIsolationTestCase(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")

        # Create a community for each user
        self.community1 = Community.objects.create(name="Community 1", owner=self.user1)
        self.community2 = Community.objects.create(name="Community 2", owner=self.user2)

        # Add users to their respective communities
        self.community1.members.add(self.user1)
        self.community2.members.add(self.user2)

    def test_community_isolation(self):
        # User 1 creates an item
        item = Item.objects.create(name="Test Item", owner=self.user1)

        # User 1 creates a subscription
        subscription = Subscription.objects.create(
            name="Test Subscription", owner=self.user1
        )

        # Verify that User 2 cannot see User 1's item
        available_items = get_items_available_for_lease(self.user2)
        self.assertNotIn(item, available_items)

        # Verify that User 2 cannot see User 1's subscription
        available_subscriptions = get_subscriptions_available_for_share(self.user2)
        self.assertNotIn(subscription, available_subscriptions)

    def tearDown(self):
        # Clean up created objects
        User.objects.all().delete()
        Community.objects.all().delete()
        Item.objects.all().delete()
        Subscription.objects.all().delete()


class LeaseE2ETest(TestCase):
    def setUp(self):

        # Create two users
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")

        # Create a community
        self.community = Community.objects.create(
            name="Test Community", owner=self.user1
        )

        # Add users to the community
        self.community.members.add(self.user1, self.user2)

        # Create an item for user1
        self.item = Item.objects.create(name="Test Item", owner=self.user1)

        # Set up date ranges
        self.today = timezone.now()
        self.five_days_ago = self.today - timedelta(days=5)
        self.five_days_later = self.today + timedelta(days=5)

    def create_lease(self, start_date, end_date):
        return Lease.objects.create(
            item=self.item, lessee=self.user2, start_date=start_date, end_date=end_date
        )

    def test_lease_scenarios(self):
        # Create initial lease
        self.create_lease(self.five_days_ago, self.five_days_later)
        self.assertEqual(Lease.objects.count(), 1)

        # Test: lease request from today to tomorrow (should be rejected)
        with self.assertRaises(ValidationError):
            self.create_lease(self.today, self.today + timedelta(days=1))
        self.assertEqual(Lease.objects.count(), 1)  # No new lease created

        # Test: lease request from 2 days ago to now (should be rejected)
        with self.assertRaises(ValidationError):
            self.create_lease(self.today - timedelta(days=2), self.today)
        self.assertEqual(Lease.objects.count(), 1)

        # Test: lease request from 4 days after today to 10 days after (should be rejected)
        with self.assertRaises(ValidationError):
            self.create_lease(
                self.today + timedelta(days=4), self.today + timedelta(days=10)
            )
        self.assertEqual(Lease.objects.count(), 1)

        # Test: lease request from 6 days after to 10 days after (should be accepted)
        self.create_lease(
            self.today + timedelta(days=6), self.today + timedelta(days=10)
        )
        self.assertEqual(Lease.objects.count(), 2)  # New lease created

    def tearDown(self):
        # Clean up created objects
        Lease.objects.all().delete()
        Item.objects.all().delete()
        self.community.delete()
        User.objects.all().delete()


class ItemRequestTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.item = Item.objects.create(name="Test Item", owner=self.user1)

    def test_item_request(self):
        self.client.login(username="user2", password="password2")
        response = self.client.post(
            reverse("item_request", kwargs={"pk": self.item.pk}),
            {"message": "Can I borrow this item?"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ItemRequest.objects.filter(item=self.item, requester=self.user2).exists())

    def tearDown(self):
        ItemRequest.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()


class SubscriptionRequestTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.subscription = Subscription.objects.create(name="Test Subscription", owner=self.user1)

    def test_subscription_request(self):
        self.client.login(username="user2", password="password2")
        response = self.client.post(
            reverse("subscription_request", kwargs={"pk": self.subscription.pk}),
            {"message": "Can you share this subscription?"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SubscriptionRequest.objects.filter(subscription=self.subscription, requester=self.user2).exists())

    def tearDown(self):
        SubscriptionRequest.objects.all().delete()
        Subscription.objects.all().delete()
        User.objects.all().delete()
