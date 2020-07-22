from django.db import models


class Commodity(models.Model):
    version = models.CharField(max_length=32)
    code = models.CharField(max_length=10)
    suffix = models.CharField(max_length=2)
    description = models.TextField()
    level = models.IntegerField()
    indent = models.IntegerField()
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    is_leaf = models.BooleanField(default=False)
    sid = models.IntegerField()
    parent_sid = models.IntegerField(null=True)

    @property
    def full_description(self):
        if not self.parent or self.level <= 4:
            return self.description
        return f"{self.parent.full_description} - {self.description}"
