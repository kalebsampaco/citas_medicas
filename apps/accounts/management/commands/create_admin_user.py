from apps.accounts.models.plan import Plan
from apps.accounts.models.role import Role
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create a super admin user with SUPER_ADMIN role"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Create or get SUPER_ADMIN role (system role, no company)
        role, created = Role.objects.get_or_create(
            name='Super Admin',
            role_type='SUPER_ADMIN',
            company=None,
            is_system=True,
            defaults={'permissions': {}}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created SUPER_ADMIN role'))

        # Create or update superuser
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'role': role,
                'company': None
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created superuser: {username}'))
        else:
            # Update existing superuser
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.role = role
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated superuser: {username}'))

        self.stdout.write(self.style.SUCCESS(f'✓ User {username} is now SUPER_ADMIN'))
        self.stdout.write(self.style.SUCCESS(f'✓ Login credentials: {email} / {password}'))
