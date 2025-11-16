from enum import Enum

from django.db.models import TextChoices


class FoodType(Enum):
    VEG="Vegetarian"
    NON_VEG="Non-Vegetarian"

    @classmethod
    def choices(cls):
        return [(member.value, member.name) for member in cls]

class VenueBookingStatus(TextChoices):
    BOOKED = "Booked", "Booked"
    AVAILABLE = "Available", "Available"

class BookingStatus(TextChoices):
    CANCELLED = "Cancelled", "Cancelled"
    COMPLETED = "Completed", "Completed"
    ONGOING = "Ongoing", "Ongoing"