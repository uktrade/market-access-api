from django.db import migrations


def delete_download_approval_permission_and_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Download approved user").delete()

    # remove "download_barriers" Permission
    Permission = apps.get_model("auth", "Permission")
    permission = Permission.objects.get(codename="download_barriers")
    permission.delete()


# Re-add the permission and group. Users will have to be re-added to group
def undo_download_approval_deletion(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.create(name="Download approved user")

    # create a "download_barrier" Permission and add it to the group
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Barrier = apps.get_model("barriers", "Barrier")
    barrier_content_type = ContentType.objects.get_for_model(Barrier)
    download_barriers_permission, created = Permission.objects.get_or_create(
        codename="download_barriers",
        defaults={
            "name": "Can download barriers",
            "content_type": barrier_content_type,
        },
    )
    group = Group.objects.get(name="Download approved user")
    group.permissions.add(download_barriers_permission)


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0034_related_barrier_feature_flag"),
    ]

    operations = [
        migrations.RunPython(
            delete_download_approval_permission_and_group,
            undo_download_approval_deletion,
        ),
    ]
