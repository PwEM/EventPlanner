from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from apps.venue.models import VenueModel, Price, City, VenueImages, BookingModel


class Command(BaseCommand):
    help = "Creates the Vendors Group and Assigns Vendor App Permissions"

    def handle(self, *args, **options):
        group_name = "Vendors"
        group, created = Group.objects.get_or_create(name=group_name)

        if created:
            self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created. '))
        else:
            self.stdout.write(self.style.WARNING(f'Group "{group_name}" already exists. '))

        models_and_codenames = {
            VenueModel: ['add_venuemodel', 'change_venuemodel', 'delete_venuemodel', 'view_venuemodel'],
            Price: ['add_price', 'change_price', 'delete_price', 'view_price'],
            City: ['add_city', 'view_city'],
            VenueImages: ['add_venueimages', 'change_venueimages', 'delete_venueimages', 'view_venueimages'],
            BookingModel: ['view_bookingmodel', 'change_bookingmodel'],
        }

        for model, codenames in models_and_codenames.items():
            content_type = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=content_type, codename__in=codenames)
            group.permissions.add(*perms)

        self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created and permissions added.'))
