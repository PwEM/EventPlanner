from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.venue.constants import BookingStatus
from apps.venue.models import BookingModel


@receiver(pre_save, sender=BookingModel)
def update_booking_status(sender, instance, **kwargs):
    if instance.booked_for and instance.booked_for < timezone.now().date():
        instance.status = BookingStatus.COMPLETED