from django.db import migrations, models
import uuid


def gen_uuid(apps, schema_editor):
    Community = apps.get_model("backend", "Community")
    for row in Community.objects.all():
        row.invite_uuid = uuid.uuid4()
        row.save(update_fields=["invite_uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0004_item_item_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="community",
            name="invite_uuid",
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="community",
            name="invite_uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
