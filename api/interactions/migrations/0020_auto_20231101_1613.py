# Generated by Django 3.2.20 on 2023-11-01 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interactions', '0019_auto_20210329_1732'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicaldocument',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical document', 'verbose_name_plural': 'historical documents'},
        ),
        migrations.AlterModelOptions(
            name='historicalinteraction',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical interaction', 'verbose_name_plural': 'historical interactions'},
        ),
        migrations.AlterModelOptions(
            name='historicalpublicbarriernote',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical public barrier note', 'verbose_name_plural': 'historical public barrier notes'},
        ),
        migrations.AlterField(
            model_name='historicaldocument',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalinteraction',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalpublicbarriernote',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
    ]