from django.urls import path

from apps.users.views import UserProfileView, UserBookingView, UserRecentVenuesView, RecentTransactionView

app_name = 'users'
urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('bookings/', UserBookingView.as_view(), name='bookings'),
    path('recent-venues/', UserRecentVenuesView.as_view(), name='recent_venues'),
    path('recent-transactions/', RecentTransactionView.as_view(), name='recent_transactions'),
]