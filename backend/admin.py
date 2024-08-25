from django.contrib import admin

from backend.models import Subscription, Community, Item, Lease

# Register your models here.
admin.site.register(Subscription)
admin.site.register(Community)
admin.site.register(Item)
admin.site.register(Lease)
