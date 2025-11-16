from django.utils import timezone

from apps.venue.constants import BookingStatus
from apps.venue.models import BookingModel


def update_booking_statuses():
    expired_bookings = BookingModel.objects.filter(
        status=BookingStatus.ONGOING,
        booked_for__lt=timezone.now().date()
    )

    updated_count = expired_bookings.update(status=BookingStatus.COMPLETED)

    return f"Updated {updated_count} bookings to COMPLETED status"