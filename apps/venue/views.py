import os

import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView
from apps.venue.services.recommendation import recommend_venues

from apps.venue.constants import VenueBookingStatus, BookingStatus
from apps.venue.forms import BookingForm
from apps.venue.models import City, VenueModel, BookingModel, KhaltiTransaction
import json
import logging
from .utils import get_location_based_recommendations

logger = logging.getLogger(__name__)

# Create your views here.
class CityDetail(DetailView):
    model = City
    context_object_name = 'city'
    template_name = 'venue/city_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get('slug')
        city = get_object_or_404(City.objects.prefetch_related("venues"), slug=slug)
        other_cities = City.objects.exclude(slug=slug)
        context.update({
            'city': city,
            'other_cities': other_cities,
        })

        return context


# class VenueDetail(DetailView):
#     model = VenueModel
#     context_object_name = 'venue'
#     template_name = 'venue/venue_detail.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         slug = self.kwargs.get('slug')
#         venue = get_object_or_404(VenueModel.objects.prefetch_related("images", "prices"), slug=slug)

#         try:
#             # Get all three recommendation types
#             recommendations = recommend_venues(venue.id, n_recommendations=5)
#         except Exception as e:
#             logger.error(f"KNN recommendation error: {e}")
#             # Fallback: just same city venues
#             recommendations = {
#                 "similar": VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
#                 "same_location": VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
#                 "price_match": VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
#             }

#         context.update({
#             'venue': venue,
#             'similar_venues': recommendations.get("similar"),
#             'same_location_venues': recommendations.get("same_location"),
#             'price_match_venues': recommendations.get("price_match"),
#         })
#         return context

class VenueDetail(DetailView):
    model = VenueModel
    context_object_name = 'venue'
    template_name = 'venue/venue_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        venue = get_object_or_404(VenueModel.objects.prefetch_related("images", "prices"), slug=slug)

        # Get user location from session or cookies (if stored from frontend)
        user_lat = self.request.session.get('user_lat')
        user_lng = self.request.session.get('user_lng')
        
        # Alternative: get from request parameters (if passed from frontend)
        if not user_lat or not user_lng:
            user_lat = self.request.GET.get('lat')
            user_lng = self.request.GET.get('lng')
            
            if user_lat and user_lng:
                try:
                    user_lat = float(user_lat)
                    user_lng = float(user_lng)
                    # Store in session for future requests
                    self.request.session['user_lat'] = user_lat
                    self.request.session['user_lng'] = user_lng
                except (ValueError, TypeError):
                    user_lat = None
                    user_lng = None

        try:
            # Get location-based recommendations
            recommendations = get_location_based_recommendations(
                venue,
                user_lat=user_lat,
                user_lng=user_lng,
                n_recommendations=5,
                max_distance_km=15
            )
            print("Recommended")
        except Exception as e:
            logger.error(f"KNN recommendation error: {e}")
            # Fallback: just same city venues
            recommendations = {
                "similar": VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
                "same_location": VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
                "price_match": VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
            }
            print("Default")

        context.update({
            'venue': venue,
            'similar_venues': VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
            'same_location_venues': recommendations.get("same_location"),
            'price_match_venues': VenueModel.objects.filter(city=venue.city).exclude(slug=slug)[:5],
            'user_has_location': user_lat is not None and user_lng is not None,
        })
        return context

class CityView(TemplateView):
    template_name = 'venue/cities.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cities = City.objects.all()
        context.update({
            'cities': cities,
        })
        return context


class BookingView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect_url': '/accounts/login/?next=' + request.path
                }, status=401)
            else:
                return super().handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body) if request.body else {}
        booking_form = BookingForm(data)

        if booking_form.is_valid():
            booking = booking_form.save()

            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'message': 'Booking created successfully'
            }, status=201)
        else:
            errors = {}
            for field, field_errors in booking_form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)


class CancelBookingView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        booking_id = request.GET.get('id')

        if not booking_id:
            return JsonResponse({'success': False, 'message': 'No booking ID provided'}, status=400)

        try:
            booking = BookingModel.objects.get(id=booking_id)
            booking.status = BookingStatus.CANCELLED
            booking.save()
            return JsonResponse({'success': True, 'message': 'Booking successfully cancelled'})
        except BookingModel.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Booking not found'}, status=404)


class PayBookingView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        booking_id = kwargs.get('id')

        if not booking_id:
            return JsonResponse({'success': False, 'message': 'No booking ID provided'}, status=400)

        try:
            booking = BookingModel.objects.get(id=booking_id)
            booking.is_paid = True
            booking.save()

            url = "https://dev.khalti.com/api/v2/epayment/initiate/"

            payload = json.dumps({
                "return_url": f"http://localhost:8000{reverse('venue:payment-success')}",
                "website_url": "http://localhost:8000/",
                "amount": "1000",
                "purchase_order_id": f"{booking.id}",
                "purchase_order_name": f"Booking-{booking.id}",
                "customer_info": {
                    "name": request.user.username or "Ram Bahaadur",
                    "email": request.user.email or "test@khalti.com",
                    "phone": request.user.phone or "9800000001"
                }
            })

            headers = {
                'Authorization': f'key {os.getenv("KHALTI_LIVE_SECRET_KEY")}',
                'Content-Type': 'application/json',
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            data = response.json()
            return JsonResponse({'success': True, 'data': data})
        except BookingModel.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Booking not found'}, status=404)

class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'venue/payment_success.html'

    def get(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        pidx = request.GET.get('pidx')
        if pidx:
            transaction_id = request.GET.get('transaction_id')
            if not KhaltiTransaction.objects.filter(transaction_id=transaction_id).exists():
                tidx = request.GET.get('tidx')
                txn_id = request.GET.get('txnId')
                total_amount = request.GET.get('total_amount')
                status = request.GET.get('status')
                purchase_order_id = request.GET.get('purchase_order_id')
                purchase_order_name = request.GET.get('purchase_order_name')

                KhaltiTransaction.objects.create(
                    booking_id=purchase_order_id,
                    user=request.user,
                    transaction_id=transaction_id,
                    pidx=pidx,
                    tidx=tidx,
                    txn_id=txn_id,
                    total_amount=total_amount,
                    status=status,
                    purchase_order_id=purchase_order_id,
                    purchase_order_name=purchase_order_name,
                )
        return self.render_to_response(context)

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie 

@require_http_methods(["POST"])
@ensure_csrf_cookie
def store_user_location(request):
    """
    Store user's location in session for personalized recommendations
    """
    try:
        data = json.loads(request.body)
        lat = data.get('lat')
        lng = data.get('lng')
        
        if lat is None or lng is None:
            return JsonResponse(
                {'error': 'Latitude and longitude are required'},
                status=400
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            return JsonResponse(
                {'error': 'Invalid latitude or longitude format'},
                status=400
            )
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return JsonResponse(
                {'error': 'Invalid coordinate values'},
                status=400
            )
        
        # Store in session
        request.session['user_lat'] = lat
        request.session['user_lng'] = lng
        request.session.modified = True

        print(request.session["user_lat"])
        print(request.session["user_lng"])
        
        return JsonResponse({
            'success': True,
            'message': 'Location stored successfully',
            'location': {
                'lat': lat,
                'lng': lng
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )