# Generated by Django 4.2.16 on 2024-10-20 08:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("b04", "0005_membership"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="date_joined",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
