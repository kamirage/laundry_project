from django.contrib import admin
from .models import (CustomerProfile, ServiceType, Material, GarmentType, Order,
                     OrderItem, InspectionAct, Defect, ActDefect, ProcessingStage, Payment)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "created_at", "status", "due_date", "total_price")
    list_filter = ("status", "created_at")
    search_fields = ("number", "customer__username", "customer__first_name", "customer__last_name")
    date_hierarchy = "created_at"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "garment_type", "service", "material", "item_price")
    list_filter = ("service", "material", "garment_type")

for model in (CustomerProfile, ServiceType, Material, GarmentType, InspectionAct,
              Defect, ActDefect, ProcessingStage, Payment):
    admin.site.register(model)
