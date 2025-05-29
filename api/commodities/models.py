from django.db import models

from .utils import format_commodity_code


class Commodity(models.Model):
    version = models.CharField(max_length=32, db_index=True)
    code = models.CharField(max_length=10, db_index=True)
    suffix = models.CharField(max_length=2)
    description = models.TextField()
    level = models.IntegerField()
    indent = models.IntegerField()
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    is_leaf = models.BooleanField(default=False, db_index=True)
    sid = models.IntegerField(null=True)
    parent_sid = models.IntegerField(null=True)
    parent_code = models.CharField(null=True)

    class Meta:
        verbose_name_plural = "commodities"

    @property
    def full_description(self):
        if not self.parent or self.level <= 4:
            return self.description
        return f"{self.parent.full_description} - {self.description}"

    @property
    def trimmed_code(self):
        return format_commodity_code(self.code, separator="")
