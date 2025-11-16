from decimal import Decimal

from django.db.models import Q
from django.views.generic import TemplateView

from apps.venue.constants import FoodType, VenueBookingStatus, BookingStatus
from apps.venue.models import City, VenueModel, Price
from django.db.models import Sum, Count, ExpressionWrapper, FloatField, F


# Create your views here.
class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cities = City.objects.all()
        venues = VenueModel.objects.all()[:8]

        context.update({
            'cities': cities,
            'venues': venues,
        })

        return context

class SearchView(TemplateView):
    template_name = 'home/search_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('q')
        city = self.request.GET.get('city')
        min_capacity = self.request.GET.get('min_capacity')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        date = self.request.GET.get('date')

        qs = VenueModel.objects.all()

        cities = City.objects.all()

        if search_term:
            qs = qs.filter(Q(name__icontains=search_term) | Q(city__name__icontains=search_term))

        if city:
            qs = qs.filter(city__id=city)

        if min_capacity:
            qs = qs.filter(capacity__gte=min_capacity)

        try:
            min_price = Decimal(min_price) if min_price else None
            max_price = Decimal(max_price) if max_price else None

            if min_price and max_price:
                qs = qs.filter(
                    Q(prices__price__gte=min_price, prices__price__lte=max_price) |
                    Q(prices__price__lte=max_price, prices__price__gte=min_price)
                )
            elif min_price:
                qs = qs.filter(prices__price__gte=min_price)
            elif max_price:
                qs = qs.filter(prices__price__lte=max_price)

        except Exception as e:
            print("Price filter error:", e)

        if date:
            qs = qs.exclude(venue_bookings__booked_for=date, venue_bookings__status=BookingStatus.PENDING)

        context.update({
            "venues": qs.distinct(),
            "cities": cities,
        })
        return context

class TransportationView(TemplateView):
    template_name = 'home/transportation.html'

class CarDecorationView(TemplateView):
    template_name = 'home/car_decoration.html'

class PhotographyView(TemplateView):
    template_name = 'home/photograph.html'

class BusRentView(TemplateView):
    template_name = 'home/bus_rent.html'