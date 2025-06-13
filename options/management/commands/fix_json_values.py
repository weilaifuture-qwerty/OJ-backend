from django.core.management.base import BaseCommand
from options.models import SysOptions
from options.options import OptionDefaultValue

class Command(BaseCommand):
    help = 'Fix JSON values in SysOptions table'

    def handle(self, *args, **options):
        for option in SysOptions.objects.all():
            try:
                # Get the current value
                current_value = option.value
                
                # If it's already a dict with 'value' key, skip it
                if isinstance(current_value, dict) and 'value' in current_value:
                    self.stdout.write(self.style.SUCCESS(f'Skipping {option.key} - already in correct format'))
                    continue
                
                # If it's a string, wrap it in a dict
                if isinstance(current_value, str):
                    option.value = {"value": current_value}
                    option.save()
                    self.stdout.write(self.style.SUCCESS(f'Fixed value for {option.key}'))
                # If it's a dict but doesn't have 'value' key, add it
                elif isinstance(current_value, dict):
                    option.value = {"value": current_value}
                    option.save()
                    self.stdout.write(self.style.SUCCESS(f'Fixed dict value for {option.key}'))
                # For other types (like lists, bools, etc.), keep as is
                else:
                    self.stdout.write(self.style.SUCCESS(f'Skipping {option.key} - non-string value'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error fixing {option.key}: {str(e)}')) 