from django.contrib import admin

from apps.venue.models import VenueModel, City, VenueImages, Price, BookingModel

# Register your models here.
class UniqueVendorAdmin(admin.ModelAdmin):
    def has_venue_field(self):
        return any(f.name == "venue" for f in self.model._meta.get_fields())

    def has_owner_field(self):
        return any(f.name == "owner" for f in self.model._meta.get_fields())

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "venue" and self.has_venue_field() and request.user.is_vendor:
            kwargs["queryset"] = VenueModel.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if hasattr(request.user, "is_vendor") and request.user.is_vendor:
            if self.has_venue_field():
                queryset = queryset.filter(venue__owner=request.user)

            if self.has_owner_field():
                queryset = queryset.filter(owner=request.user)
            return queryset

        return queryset

class VenueModelAdmin(UniqueVendorAdmin):
    exclude = ("owner",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


admin.site.register(VenueModel, VenueModelAdmin)
admin.site.register(City)
admin.site.register(VenueImages, UniqueVendorAdmin)
admin.site.register(Price, UniqueVendorAdmin)
admin.site.register(BookingModel, UniqueVendorAdmin)