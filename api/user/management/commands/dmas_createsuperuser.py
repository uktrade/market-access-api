from django.contrib.auth.management.commands import createsuperuser
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError


class Command(createsuperuser.Command):
    help = "Create a new superuser or update existing user permissions"

    def handle(self, *args, **options):

        username = options["email"]

        # Check if the user already exists
        # this field USERNAME_FIELD will default to username as we do not have a custom user model
        if self.UserModel.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'User "{username}" already exists. Updating permissions...'
                )
            )
            user = self.UserModel._default_manager.get(username=username)
        else:
            try:
                # Create the superuser using the original handle method
                super().handle(*args, **options)
                user = self.UserModel._default_manager.get(username=username)
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f"Error creating user: {e}"))
                return

        # Fetch the Administrator group
        try:
            admin_group = Group.objects.get(name="Administrator")
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR("Administrator group does not exist."))
            return
        if admin_group in user.groups.all():
            self.stdout.write(
                self.style.SUCCESS(
                    f'User "{username}" is already in the Administrator group.'
                )
            )
            return
        user.groups.add(admin_group)
        self.stdout.write(
            self.style.SUCCESS(f'User "{username}" added to the Administrator group.')
        )
