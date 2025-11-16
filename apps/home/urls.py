from django.urls import path

from apps.home.views import HomeView, SearchView, CarDecorationView, PhotographyView, BusRentView, TransportationView

app_name = "home"

urlpatterns = [
    path('', HomeView.as_view(), name='index'),
    path('search', SearchView.as_view(), name='search'),

    path('transporation/', TransportationView.as_view(), name='transportation'),
    path('car-decoration/', CarDecorationView.as_view(), name='car-decoration'),
    path('photographer/', PhotographyView.as_view(), name='photographer'),

    path('bus-rent/', BusRentView.as_view(), name='bus-rent'),
]