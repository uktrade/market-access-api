from django.db import models


class Commodity(models.Model):
    code = models.CharField(max_length=10)
    suffix = models.CharField(max_length=2)
    description = models.TextField()
    level = models.IntegerField()
    indent = models.IntegerField()
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    def full_name(self):
        if not self.parent:
            return self.name
        return f"{self.parent.name} - {self.name}"
