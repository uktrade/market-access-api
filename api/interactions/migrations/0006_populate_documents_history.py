from django.db import connection, migrations


def populate_documents_history(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE interactions_historicalinteraction hi1
            SET documents_cache = sq.documents
            FROM (
                SELECT
                hi2.history_id,
                ARRAY_AGG(
                    json_build_object('id', intdoc.document_id, 'name', doc.original_filename)
                ) AS documents
                FROM interactions_historicalinteraction hi2
                JOIN interactions_interaction_documents intdoc
                ON intdoc.interaction_id = hi2.id
                JOIN interactions_document doc
                ON doc.id = intdoc.document_id
                GROUP BY hi2.history_id
            ) AS sq
            WHERE hi1.history_id=sq.history_id
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ('interactions', '0005_auto_20200320_0941'),
    ]

    operations = [
        migrations.RunPython(
            populate_documents_history,
            reverse_code=migrations.RunPython.noop
        ),
    ]
