from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from apps.users.models import AuthUser
from django.contrib.auth.models import Group
from django.shortcuts import reverse
from django.urls import path

# Register your models here.
class AuthUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'is_vendor', 'approve_button')
    actions = ['make_vendor']

    @admin.action(description="Approve selected users to Vendors Group")
    def make_vendor(self, request, queryset):
        group, created = Group.objects.get_or_create(name='Vendors')
        queryset.update(is_active=True)
        group.user_set.add(*queryset)
        self.message_user(request, f"Approved {queryset.count()} users to Vendors Group")


    @admin.display(description="Approve Vendor")
    def approve_button(self, obj):
        if obj.is_vendor and not obj.is_staff:
            url = reverse('admin:approve_vendor', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Approve</a>',
                url
            )

        if not obj.is_staff or obj.is_superuser:
            return ""

        return "Approved"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
              '<int:user_id>/approve/',
                self.admin_site.admin_view(self.approve_vendor),
                name="approve_vendor"
            ),
        ]
        return custom_urls + urls

    def approve_vendor(self, request, user_id):
        user = self.get_object(request, user_id)
        user.is_active = True
        user.is_staff = True
        user.save()
        self.message_user(request, f"Approved {user.username} users to Vendors Group")
        return HttpResponseRedirect(reverse('admin:users_authuser_changelist'))


admin.site.register(AuthUser, AuthUserAdmin)