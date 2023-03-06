from django.contrib import admin
from .models import Item, Warehouse, ItemsForStorage, Client, CustomersItems

class ItemsForStorageInline(admin.TabularInline):
    model = ItemsForStorage
    extra = 1

class ItemsInline(admin.TabularInline):
    model = CustomersItems
    extra = 1

class WarehouseAdmin(admin.ModelAdmin):
    inlines = [ItemsForStorageInline]

class ClientAdmin(admin.ModelAdmin):
    inlines = [ItemsInline]

admin.site.register(Item)
admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Client, ClientAdmin)
