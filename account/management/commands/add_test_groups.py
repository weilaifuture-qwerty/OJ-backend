from django.core.management.base import BaseCommand
from account.models import User, UserProfile, AdminType
from django.db import transaction

class Command(BaseCommand):
    help = 'Add test student groups to existing users'

    def handle(self, *args, **kwargs):
        groups = ["Class A", "Class B", "Class C", "Advanced", "Beginners"]
        
        with transaction.atomic():
            # Get all regular users (students)
            students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
            
            if not students.exists():
                self.stdout.write(self.style.WARNING('No students found. Creating test students...'))
                
                # Create some test students
                for i in range(1, 16):
                    user = User.objects.create(
                        username=f'student{i}',
                        email=f'student{i}@example.com',
                        admin_type=AdminType.REGULAR_USER
                    )
                    user.set_password('password123')
                    user.save()
                    
                    # Create profile with group
                    group = groups[(i-1) % len(groups)]
                    UserProfile.objects.create(
                        user=user,
                        real_name=f'Student {i}',
                        student_group=group
                    )
                    
                self.stdout.write(self.style.SUCCESS(f'Created 15 test students with groups'))
            else:
                # Assign groups to existing students
                updated = 0
                for i, student in enumerate(students):
                    profile, created = UserProfile.objects.get_or_create(user=student)
                    if not profile.student_group:
                        profile.student_group = groups[i % len(groups)]
                        profile.save()
                        updated += 1
                
                self.stdout.write(self.style.SUCCESS(f'Updated {updated} students with groups'))
            
            # Show group distribution
            self.stdout.write('\nGroup Distribution:')
            for group in groups:
                count = UserProfile.objects.filter(
                    user__admin_type=AdminType.REGULAR_USER,
                    student_group=group
                ).count()
                self.stdout.write(f'  {group}: {count} students')