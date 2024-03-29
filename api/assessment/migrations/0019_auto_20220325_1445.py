# Generated by Django 3.2.12 on 2022-03-25 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0018_auto_20201130_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='economicimpactassessment',
            name='impact',
            field=models.PositiveIntegerField(choices=[(1, '1: £ thousands'), (2, '2: £ tens of thousands'), (3, '3: £ hundreds of thousands (£100k - £999k)'), (4, '4: £ low hundreds of thousands (£100k-£400k)'), (5, '5: £ mid hundreds of thousands (£400k-£700k)'), (6, '6: £ high hundreds of thousands (£700k-£999k)'), (7, '7: £ millions (£1m-£9.9m)'), (8, '8: £ low millions (£1m-£4m)'), (9, '9: £ mid millions (£4m-£7m)'), (10, '10: £ high millions (£7m-£9.9m)'), (11, '11: £ tens of millions (£10m-£99m)'), (12, '12: £ low tens of millions (£10m-£40m)'), (13, '13: £ mid tens of millions (£40m-£70m)'), (14, '14: £ high tens of millions (£70m-£99m)'), (15, '15: £ hundreds of millions (£100m-£999m)'), (16, '16: £ low hundreds of millions (£100m-£400m)'), (17, '17: £ mid hundreds of millions (£400m-£700m)'), (18, '18: £ high hundreds of millions (£700m-£999m)'), (19, '19: £ billions (£1bn-£9.9bn)'), (20, '20: £ low billions (£1bn-£4bn)'), (21, '21: £ mid billions (£4bn-£7bn)'), (22, '22: £ high billions (£7bn-£9.9bn)'), (23, '23: £ tens of billions (£10bn-£20bn)'), (24, '24: £ low tens of billions (£10bn-£15bn)'), (25, '25: £ high tens of billions (£15bn-£20bn)')]),
        ),
        migrations.AlterField(
            model_name='historicaleconomicimpactassessment',
            name='impact',
            field=models.PositiveIntegerField(choices=[(1, '1: £ thousands'), (2, '2: £ tens of thousands'), (3, '3: £ hundreds of thousands (£100k - £999k)'), (4, '4: £ low hundreds of thousands (£100k-£400k)'), (5, '5: £ mid hundreds of thousands (£400k-£700k)'), (6, '6: £ high hundreds of thousands (£700k-£999k)'), (7, '7: £ millions (£1m-£9.9m)'), (8, '8: £ low millions (£1m-£4m)'), (9, '9: £ mid millions (£4m-£7m)'), (10, '10: £ high millions (£7m-£9.9m)'), (11, '11: £ tens of millions (£10m-£99m)'), (12, '12: £ low tens of millions (£10m-£40m)'), (13, '13: £ mid tens of millions (£40m-£70m)'), (14, '14: £ high tens of millions (£70m-£99m)'), (15, '15: £ hundreds of millions (£100m-£999m)'), (16, '16: £ low hundreds of millions (£100m-£400m)'), (17, '17: £ mid hundreds of millions (£400m-£700m)'), (18, '18: £ high hundreds of millions (£700m-£999m)'), (19, '19: £ billions (£1bn-£9.9bn)'), (20, '20: £ low billions (£1bn-£4bn)'), (21, '21: £ mid billions (£4bn-£7bn)'), (22, '22: £ high billions (£7bn-£9.9bn)'), (23, '23: £ tens of billions (£10bn-£20bn)'), (24, '24: £ low tens of billions (£10bn-£15bn)'), (25, '25: £ high tens of billions (£15bn-£20bn)')]),
        ),
    ]
