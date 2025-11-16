# Create your views here.
import json

from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView, ListView

from apps.users.forms import UserProfileForm
from apps.venue.models import BookingModel, VenueModel, VenueRatingModel, KhaltiTransaction


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserProfileForm
    template_name = 'users/user_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('users:profile')

class UserBookingView(LoginRequiredMixin, ListView):
    template_name = 'users/user_bookings.html'
    model = BookingModel
    context_object_name = "bookings"

    def get_queryset(self):
        return BookingModel.objects.filter(user=self.request.user, is_paid=True).order_by('-booked_at')

class UserRecentVenuesView(LoginRequiredMixin, ListView):
    template_name = 'users/user_recent_venues.html'
    model = VenueModel
    context_object_name = "recent_venues"

    def get_queryset(self):
        return VenueModel.objects.filter(venue_bookings__user=self.request.user).distinct()

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        rating = data.get('rating')
        user = request.user
        venue_id = data.get('venue_id')

        VenueRatingModel.objects.create(
            user=user,
            venue_id=venue_id,
            rating=rating,
        )

        return JsonResponse({
            "success": True,
        })

class RecentTransactionView(LoginRequiredMixin, ListView):
    template_name = 'users/user_recent_transactions.html'

    def get_queryset(self):
        return KhaltiTransaction.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "recent_transactions": self.get_queryset(),
        })
        return context