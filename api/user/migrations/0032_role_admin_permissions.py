from django.db import migrations


def assign_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")

    Group.objects.create(name="Role administrator")

    role_admin_group = Group.objects.get(name="Role administrator")
    change_user_permission = Permission.objects.get(codename="change_user")
    list_users_permission = Permission.objects.get(codename="list_users")

    role_admin_group.permissions.add(change_user_permission)
    role_admin_group.permissions.add(list_users_permission)

    administrator_group = Group.objects.get(name="Administrator")
    delete_users_permission = Permission.objects.get(codename="delete_profile")
    administrator_group.permissions.add(delete_users_permission)


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0031_alter_useractivitylog_event_type"),
    ]

    operations = [
        migrations.RunPython(
            assign_permissions, reverse_code=migrations.RunPython.noop
        ),
    ]
