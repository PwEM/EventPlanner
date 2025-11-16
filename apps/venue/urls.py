from django.urls import path
from .views import CityDetail, VenueDetail, CityView, BookingView, CancelBookingView, PayBookingView, PaymentSuccessView

app_name = "venue"
urlpatterns = [
    path('city/<slug:slug>/', CityDetail.as_view(), name='city-detail'),
    path('cities/', CityView.as_view(), name='cities'),
    path('<slug:slug>/', VenueDetail.as_view(), name='venue-detail'),
    path('booking/<int:venue_id>/', BookingView.as_view(), name='booking'),
    path('cancel-booking', CancelBookingView.as_view(), name='cancel-booking'),
    path('pay-booking/<int:id>/', PayBookingView.as_view(), name='pay-booking'),
    path('payment/sucess/', PaymentSuccessView.as_view(), name='payment-success'),
]