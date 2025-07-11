# Generated by Django 5.2.3 on 2025-06-23 12:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('medical_stores', '0003_remove_medicalstore_devices_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', models.JSONField(default=list)),
                ('tax', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('store', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medical_stores.medicalstore')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
