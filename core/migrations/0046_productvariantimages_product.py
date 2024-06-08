# Generated by Django 4.2.4 on 2023-10-15 10:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0045_productvariantimages"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariantimages",
            name="product",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.product",
            ),
            preserve_default=False,
        ),
    ]