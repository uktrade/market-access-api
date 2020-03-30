from django.contrib import admin

from api.metadata.models import Category


class CategoryAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing Category edits.
    """

    list_display = ("title", "category")


admin.site.register(Category, CategoryAdmin)
