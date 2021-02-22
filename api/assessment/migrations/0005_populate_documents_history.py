from django.db import connection, migrations


def populate_documents_history(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE assessment_historicalassessment ha1
            SET documents_cache = sq.documents
            FROM (
                SELECT
                ha2.history_id,
                ARRAY_AGG(
                    json_build_object('id', ad.document_id, 'name', doc.original_filename)
                ) AS documents
                FROM assessment_historicalassessment ha2
                JOIN assessment_assessment_documents ad
                ON ad.assessment_id = ha2.id
                JOIN interactions_document doc
                ON doc.id = ad.document_id
                GROUP BY ha2.history_id
            ) AS sq
            WHERE ha1.history_id=sq.history_id
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("assessment", "0004_historicalassessment_documents_cache"),
    ]

    operations = [
        migrations.RunPython(
            populate_documents_history, reverse_code=migrations.RunPython.noop
        ),
    ]
