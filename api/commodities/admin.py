from django.contrib import admin

from api.commodities.models import Commodity


class CommodityAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "description",
        "indent",
        "parent_code",
        "version",
    )
    search_fields = ("code",)
    ordering = ("code",)


admin.site.register(Commodity, CommodityAdmin)
