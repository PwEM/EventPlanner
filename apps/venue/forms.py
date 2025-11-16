from django import forms
from django.utils import timezone

from apps.venue.constants import BookingStatus
from apps.venue.models import BookingModel


class BookingForm(forms.ModelForm):
    class Meta:
        model = BookingModel
        fields = "__all__"
        widgets = {
            'booked_for': forms.DateInput(attrs={'type': 'date'}),  # Ensures date picker in browser
        }

    def clean(self):
        cleaned_data = super().clean()
        total_people = cleaned_data.get('total_people')
        venue = cleaned_data.get('venue')
        booked_for = cleaned_data.get('booked_for')

        if booked_for and booked_for < timezone.now().date():
            if not self.instance.pk:
                self.add_error('booked_for', "Booking date must be in the future.")
            else:
               cleaned_data['status'] = BookingStatus.COMPLETED

        if venue and total_people:
            if total_people > venue.capacity:
                self.add_error('total_people', f"The venue can only accommodate up to {venue.capacity} people.")

        if venue and booked_for:
            is_booked = BookingModel.objects.filter(
                venue=venue,
                booked_for=booked_for,
                status=BookingStatus.ONGOING
            ).exists()
            if is_booked:
                self.add_error("booked_for", f"The venue is already booked for {booked_for}")

        return cleaned_data

    def clean_booked_for(self):
        booked_for = self.cleaned_data.get('booked_for')
        if booked_for and booked_for < timezone.now().date():
            raise forms.ValidationError("Booking date must be in the future.")
        return booked_for

