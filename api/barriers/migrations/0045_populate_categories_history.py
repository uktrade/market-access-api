from django.db import connection, migrations


def populate_categories_history(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE barriers_historicalbarrierinstance hb1
            SET categories_cache = sq.categories
            FROM (
                SELECT hb2.history_id, ARRAY_AGG(bc.category_id) AS categories
                FROM barriers_historicalbarrierinstance hb2
                JOIN barriers_barrierinstance_categories bc
                ON bc.barrierinstance_id = hb2.id
                GROUP BY hb2.history_id
            ) AS sq
            WHERE hb1.history_id=sq.history_id
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ('barriers', '0044_auto_20200325_1220'),
        ('metadata', '0012_auto_20200318_1036'),
    ]

    operations = [
        migrations.RunPython(
            populate_categories_history,
            reverse_code=migrations.RunPython.noop
        ),
    ]
