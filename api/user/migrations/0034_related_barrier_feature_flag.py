from django.db import migrations


def add_related_barrier_permission(app, schema_editor):
    Permission = app.get_model("auth", "Permission")
    Group = app.get_model("auth", "Group")
    ContentType = app.get_model("contenttypes", "ContentType")
    User = app.get_model("auth", "User")

    user_content_type = ContentType.objects.get_for_model(User)

    related_barrier_user, created = Permission.objects.get_or_create(
        codename="related_barrier_user",
        defaults={
            "name": "Can view related barriers",
            "content_type": user_content_type,
        },
    )

    group, created = Group.objects.get_or_create(name="Related Barriers")
    group.permissions.add(
        related_barrier_user,
    )


def delete_related_barrier_permission(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    related_barrier_user = Permission.objects.get(
        codename="related_barrier_user",
    )
    related_barrier_user.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0033_auto_20231122_1312"),
    ]

    operations = [
        migrations.RunPython(
            code=add_related_barrier_permission,
            reverse_code=delete_related_barrier_permission,
        ),
    ]
