# Generated by Django 4.2.4 on 2023-11-18 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_architecture_architectureimages'),
    ]

    operations = [
        migrations.AddField(
            model_name='sub_categories',
            name='youtube_link',
            field=models.CharField(default=1, max_length=1000),
            preserve_default=False,
        ),
    ]
