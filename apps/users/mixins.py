from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect


class VendorPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that restricts access to authenticated users
    who are marked as vendors and are part of the Vendors group.
    """

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_vendor and user.groups.filter(name="Vendors").exists()

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page. Vendors only.")
        return redirect("home:index")