from django.db import migrations


def add_permission_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    approver_group = Group.objects.create(name="Public barrier approver")

    change_barrier_public_eligibility = Permission.objects.get(
        codename="change_barrier_public_eligibility",
    )
    change_publicbarrier = Permission.objects.get(
        codename="change_publicbarrier",
    )
    mark_barrier_as_ready_for_publishing = Permission.objects.get(
        codename="mark_barrier_as_ready_for_publishing",
    )

    approver_group.permissions.add(
        change_barrier_public_eligibility,
        change_publicbarrier,
        mark_barrier_as_ready_for_publishing,
    )


def delete_permission_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for group_name in ["Sifter", "Editor"]:
        group_to_delete = Group.objects.filter(name=group_name)
        group_to_delete.delete()


def reverse_role_addition(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    approver_group = Group.objects.get(name="Public barrier approver")
    approver_group.delete()


def reverse_group_deletion(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    sifter_group = Group.objects.create(name="Sifter")
    editor_group = Group.objects.create(name="Editor")

    change_barrier_public_eligibility = Permission.objects.get(
        codename="change_barrier_public_eligibility",
    )
    change_publicbarrier = Permission.objects.get(
        codename="change_publicbarrier",
    )
    mark_barrier_as_ready_for_publishing = Permission.objects.get(
        codename="mark_barrier_as_ready_for_publishing",
    )

    sifter_group.permissions.add(
        change_barrier_public_eligibility,
        change_publicbarrier,
        mark_barrier_as_ready_for_publishing,
    )

    editor_group.permissions.add(
        change_barrier_public_eligibility,
        change_publicbarrier,
        mark_barrier_as_ready_for_publishing,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0035_delete_download_approval_permission"),
    ]

    operations = [
        migrations.RunPython(
            delete_permission_groups, reverse_code=reverse_group_deletion
        ),
        migrations.RunPython(add_permission_group, reverse_code=reverse_role_addition),
    ]
