from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_petinvite'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkin',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='checkins/'),
        ),
    ]
