from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from backend.models import Community, Item, Subscription, Lease, Request
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


class RequestE2ETest(TestCase):
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

    def test_create_request(self):
        # User 1 creates a request
        request = Request.objects.create(
            name="Test Request",
            request_type=Request.ITEM,
            owner=self.user1,
        )
        request.shared_with.add(self.community)

        self.assertEqual(Request.objects.count(), 1)
        self.assertEqual(request.name, "Test Request")
        self.assertEqual(request.request_type, Request.ITEM)
        self.assertEqual(request.owner, self.user1)
        self.assertIn(self.community, request.shared_with.all())

    def test_update_request(self):
        # User 1 creates a request
        request = Request.objects.create(
            name="Test Request",
            request_type=Request.ITEM,
            owner=self.user1,
        )
        request.shared_with.add(self.community)

        # User 1 updates the request
        request.name = "Updated Request"
        request.request_type = Request.SUBSCRIPTION
        request.save()

        updated_request = Request.objects.get(pk=request.pk)
        self.assertEqual(updated_request.name, "Updated Request")
        self.assertEqual(updated_request.request_type, Request.SUBSCRIPTION)

    def test_delete_request(self):
        # User 1 creates a request
        request = Request.objects.create(
            name="Test Request",
            request_type=Request.ITEM,
            owner=self.user1,
        )
        request.shared_with.add(self.community)

        # User 1 deletes the request
        request.delete()

        self.assertEqual(Request.objects.count(), 0)

    def tearDown(self):
        # Clean up created objects
        Request.objects.all().delete()
        Community.objects.all().delete()
        User.objects.all().delete()


class RequestListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.community = Community.objects.create(name="Test Community", owner=self.user1)
        self.community.members.add(self.user1, self.user2)
        self.request1 = Request.objects.create(name="Request 1", request_type=Request.ITEM, owner=self.user1)
        self.request2 = Request.objects.create(name="Request 2", request_type=Request.SUBSCRIPTION, owner=self.user2)
        self.request1.shared_with.add(self.community)
        self.request2.shared_with.add(self.community)

    def test_request_list_view(self):
        self.client.login(username="user1", password="password1")
        response = self.client.get(reverse("request_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request 1")
        self.assertContains(response, "Request 2")

    def tearDown(self):
        Request.objects.all().delete()
        Community.objects.all().delete()
        User.objects.all().delete()


class RequestCompletionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")
        self.community = Community.objects.create(name="Test Community", owner=self.user1)
        self.community.members.add(self.user1, self.user2)
        self.request1 = Request.objects.create(name="Request 1", request_type=Request.ITEM, owner=self.user1)
        self.request2 = Request.objects.create(name="Request 2", request_type=Request.SUBSCRIPTION, owner=self.user2)
        self.request1.shared_with.add(self.community)
        self.request2.shared_with.add(self.community)

    def test_only_owner_can_mark_completed(self):
        self.client.login(username="user2", password="password2")
        response = self.client.post(reverse("request_update", args=[self.request1.pk]), {
            "name": self.request1.name,
            "request_type": self.request1.request_type,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, 403)  # Forbidden

        self.client.login(username="user1", password="password1")
        response = self.client.post(reverse("request_update", args=[self.request1.pk]), {
            "name": self.request1.name,
            "request_type": self.request1.request_type,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.request1.refresh_from_db()
        self.assertTrue(self.request1.is_completed)

    def test_completed_requests_not_visible_to_others(self):
        self.request1.is_completed = True
        self.request1.save()

        self.client.login(username="user2", password="password2")
        response = self.client.get(reverse("request_list"))
        self.assertNotContains(response, "Request 1")
        self.assertContains(response, "Request 2")

    def tearDown(self):
        Request.objects.all().delete()
        Community.objects.all().delete()
        User.objects.all().delete()
