# Generated by Django 3.2.16 on 2022-11-23 16:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('barriers', '0134_migrate_unknown_barriers_to_open'),
    ]

    operations = [
        migrations.CreateModel(
            name='BarrierTopPrioritySummary',
            fields=[
                ('top_priority_summary_text', models.TextField(blank=True)),
                ('created_on', models.DateTimeField(blank=True, null=True)),
                ('modified_on', models.DateTimeField(blank=True, null=True)),
                ('barrier', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='top_priority_summary', serialize=False, to='barriers.barrier')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='top_priority_summary_submit_user', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='top_priority_summary_modify_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
