# Generated by Django 4.2.4 on 2024-03-23 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0107_remove_productvarient_gst_rate_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="main_category",
            name="active_status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("disabled", "Disabled"),
                    ("rejected", "Rejected"),
                    ("in_review", "In Review"),
                    ("published", "Published"),
                ],
                default="in_review",
                max_length=10,
            ),
        ),
    ]
