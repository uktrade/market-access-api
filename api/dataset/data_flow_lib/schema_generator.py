from django.db.models import Model
from django.db.models import fields
from django.db.models.fields import related
from django.db.models.fields.json import JSONField
from django.contrib.postgres.fields.array import ArrayField


FIELD_TO_TYPE = {
    fields.DateTimeField: 'timestamp',
    fields.DateField: 'timestamp',
    fields.CharField: 'varchar',
    fields.UUIDField: 'varchar',
    fields.BooleanField: 'boolean',
    fields.TextField: 'varchar',
    fields.PositiveIntegerField: 'int',
    fields.SmallIntegerField: 'int',
    fields.BigIntegerField: 'bigint',
    fields.AutoField: 'varchar',
    JSONField: 'json',
    ArrayField: 'array',
    related.ForeignKey: 'varchar',
    related.OneToOneField: 'varchar',
}


def generate_schema(model: Model):
    """
    Converts a list of Django Model fields to a Dict representation of its typing.

    Example use:

        from api.barriers.models import Barrier
        schema: List[Dict] = generate_schema(Barrier)
        print(schema)
    """
    columns = []

    for field in model._meta.concrete_fields:
        field_schema = {}

        field_schema["name"] = field.__dict__["name"]
        field_schema["type"] = FIELD_TO_TYPE[type(field)]
        if not field.__dict__["null"]:
            field_schema["nullable"] = False

        columns.append(field_schema)

    return columns
