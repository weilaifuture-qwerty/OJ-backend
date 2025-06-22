from django.core.management.base import BaseCommand
from django.utils import timezone
from account.models import UserProfile


class Command(BaseCommand):
    help = 'Clear expired user moods'

    def handle(self, *args, **options):
        """Clear moods that have passed their clear time"""
        expired_profiles = UserProfile.objects.filter(
            mood_clear_at__lte=timezone.now(),
            mood_clear_at__isnull=False
        )
        
        count = expired_profiles.count()
        
        if count > 0:
            expired_profiles.update(
                status_message='',
                mood_emoji='',
                mood_clear_at=None,
                # Keep status and color
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared {count} expired moods')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No expired moods to clear')
            )