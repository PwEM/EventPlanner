from django.core.management import BaseCommand
from apps.venue.tasks import update_booking_statuses

class Command(BaseCommand):
    help = 'Updates booking statuses to COMPLETED if booked_for date passed'

    def handle(self, *args, **options):
        update_booking_statuses()
        self.stdout.write("Updated booking statuses")