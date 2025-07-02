from django.contrib import admin
from .models import ShippingConfig, TaxConfig


@admin.register(ShippingConfig)
class ShippingConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_distance_km', 'cost', 'is_active')
    list_editable = ('cost', 'is_active')
    ordering = ('max_distance_km',)

@admin.register(TaxConfig)
class TaxConfigAdmin(admin.ModelAdmin):
    list_display = ('region_name', 'tax_rate_percentage', 'is_active')
    list_editable = ('is_active',)
    
    def tax_rate_percentage(self, obj):
        return f"{float(obj.tax_rate)*100:.2f}%"
    tax_rate_percentage.short_description = 'Tax Rate'
# Register your models here.
