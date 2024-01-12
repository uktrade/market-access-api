from django.db import migrations


def assign_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")

    Group.objects.create(name="Role administrator")

    role_admin_group = Group.objects.get(name="Role administrator")
    change_user_permission = Permission.objects.get(codename="change_user")
    list_users_permission = Permission.objects.get(codename="list_users")
    region_lead_permission = Permission.objects.get(codename="set_regionallead")

    role_admin_group.permissions.add(change_user_permission)
    role_admin_group.permissions.add(list_users_permission)
    role_admin_group.permissions.add(region_lead_permission)

    administrator_group = Group.objects.get(name="Administrator")
    delete_users_permission = Permission.objects.get(codename="delete_profile")
    administrator_group.permissions.add(delete_users_permission)


def reverse_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")

    permission = Permission.objects.get(codename="delete_profile")

    admin_group = Group.objects.get(name="Administrator")
    admin_group.permissions.remove(permission)

    role_admin_group = Group.objects.get(name="Role administrator")
    change_user_permission = Permission.objects.get(codename="change_user")
    list_users_permission = Permission.objects.get(codename="list_users")
    region_lead_permission = Permission.objects.get(codename="set_regionallead")
    role_admin_group.permissions.remove(change_user_permission)
    role_admin_group.permissions.remove(list_users_permission)
    role_admin_group.permissions.remove(region_lead_permission)
    role_admin_group.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0031_alter_useractvitiylog_event_type"),
    ]

    operations = [
        migrations.RunPython(assign_permissions, reverse_code=reverse_permissions),
    ]
