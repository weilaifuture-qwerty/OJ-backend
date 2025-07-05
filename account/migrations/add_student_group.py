# Generated migration for adding student_group field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='student_group',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]