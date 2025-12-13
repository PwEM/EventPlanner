from math import radians, cos, sin, asin, sqrt
from apps.venue.models import VenueModel
import joblib
import logging
from django.conf import settings
import os
from scipy.sparse import csr_matrix, hstack


logger = logging.getLogger(__name__)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6371 * c
    return km


def get_location_based_recommendations(venue, user_lat=None, user_lng=None, n_recommendations=5, max_distance_km=15):
    """
    Get venue recommendations based on the current venue and optionally user's location
    
    Args:
        venue: Current VenueModel instance
        user_lat: User's latitude (optional)
        user_lng: User's longitude (optional)
        n_recommendations: Number of recommendations to return
        max_distance_km: Maximum distance in kilometers
    
    Returns:
        dict with recommendation categories
    """
    MODEL_DIR = getattr(settings, "KNN_MODEL_DIR", os.path.join(settings.BASE_DIR, "knn_models"))
    
    try:
        # Load models
        knn = joblib.load(os.path.join(MODEL_DIR, "knn_venues.pkl"))
        ohe = joblib.load(os.path.join(MODEL_DIR, "ohe_venues.pkl"))
        price_scaler = joblib.load(os.path.join(MODEL_DIR, "price_scaler_venues.pkl"))
        location_scaler = joblib.load(os.path.join(MODEL_DIR, "location_scaler_venues.pkl"))
        venue_data = joblib.load(os.path.join(MODEL_DIR, "venue_data.pkl"))
        config = joblib.load(os.path.join(MODEL_DIR, "model_config.pkl"))
    except FileNotFoundError as e:
        logger.error(f"Model files not found: {e}")
        raise Exception("Recommendation model not found")
    
    # Determine the reference location (user location if provided, otherwise venue location)
    ref_lat = user_lat if user_lat is not None else venue.lat
    ref_lng = user_lng if user_lng is not None else venue.lng
    
    # Get venue prices
    veg_price = venue.get_veg_price or 0
    non_veg_price = venue.get_non_veg_price or 0
    
    # --- CONSISTENT DATA PREPARATION (FIXED) ---
    # Convert data into NumPy arrays before passing to transform() to avoid the UserWarning.
    # This assumes the training script used the .values fix.
    
    # ----------------------------------------------------
    # --- 1. SIMILAR VENUES (based on current venue features) ---
    # ----------------------------------------------------
    
    # FIX: Use numpy array for OHE transformation (city_id is a single value, but needs to be in a list of lists)
    city_feature = ohe.transform([[venue.city_id]])
    
    # FIX: Use numpy array for price scaler
    price_feature = price_scaler.transform([[veg_price, non_veg_price]])
    
    # FIX: Use numpy array for location scaler
    location_feature = location_scaler.transform([[venue.lat, venue.lng]])
    
    location_feature = location_feature * config.get('location_weight', 2.0)
    
    similar_features = hstack([
        csr_matrix(city_feature),
        csr_matrix(price_feature),
        csr_matrix(location_feature)
    ])
    
    distances, indices = knn.kneighbors(similar_features, n_neighbors=min(15, len(venue_data)))
    
    similar_venues = []
    # Loop for similar venues remains the same...
    for idx in indices[0]:
        venue_id = int(venue_data.iloc[idx]['id'])
        if venue_id == venue.id: 
            continue
        
        venue_lat = venue_data.iloc[idx]['lat']
        venue_lng = venue_data.iloc[idx]['lng']
        # NOTE: Make sure your haversine function is available and correct (expects lng, lat, lng, lat)
        distance = haversine(ref_lng, ref_lat, venue_lng, venue_lat)
        
        if distance <= max_distance_km:
            similar_venues.append((venue_id, distance))
    
    similar_venues = sorted(similar_venues, key=lambda x: x[1])[:n_recommendations]
    similar_venue_ids = [v[0] for v in similar_venues]
    
    # --------------------------------------------------------
    # --- 2. SAME LOCATION (nearest venues regardless of price) ---
    # --------------------------------------------------------
    
    # Focus on location, use average prices
    avg_veg = venue_data['veg_price'].mean() or 0
    avg_non_veg = venue_data['non_veg_price'].mean() or 0
    
    # FIX: Ensure all inputs to transform are arrays
    city_feature_loc = ohe.transform([[venue.city_id]])
    price_feature_loc = price_scaler.transform([[avg_veg, avg_non_veg]])
    location_feature_loc = location_scaler.transform([[ref_lat, ref_lng]])
    
    location_feature_loc = location_feature_loc * config.get('location_weight', 2.0) * 3 
    
    location_features = hstack([
        csr_matrix(city_feature_loc),
        csr_matrix(price_feature_loc),
        csr_matrix(location_feature_loc)
    ])
    
    distances, indices = knn.kneighbors(location_features, n_neighbors=min(15, len(venue_data)))
    
    same_location_venues = []
    # Loop for same location venues remains the same...
    for idx in indices[0]:
        venue_id = int(venue_data.iloc[idx]['id'])
        if venue_id == venue.id:
            continue
        
        venue_lat = venue_data.iloc[idx]['lat']
        venue_lng = venue_data.iloc[idx]['lng']
        distance = haversine(ref_lng, ref_lat, venue_lng, venue_lat)
        
        if distance <= max_distance_km:
            same_location_venues.append((venue_id, distance))
    
    same_location_venues = sorted(same_location_venues, key=lambda x: x[1])[:n_recommendations]
    same_location_venue_ids = [v[0] for v in same_location_venues]
    
    # ----------------------------------------------------
    # --- 3. PRICE MATCH (similar prices, broader location) ---
    # ----------------------------------------------------
    
    # FIX: Ensure all inputs to transform are arrays
    city_feature_price = ohe.transform([[venue.city_id]])
    price_feature_price = price_scaler.transform([[veg_price, non_veg_price]])
    location_feature_price = location_scaler.transform([[venue.lat, venue.lng]])
    
    location_feature_price = location_feature_price * config.get('location_weight', 2.0) * 0.5 
    
    price_features = hstack([
        csr_matrix(city_feature_price),
        csr_matrix(price_feature_price),
        csr_matrix(location_feature_price)
    ])
    
    distances, indices = knn.kneighbors(price_features, n_neighbors=min(15, len(venue_data)))
    
    price_match_venues = []
    # Loop for price match venues remains the same...
    for idx in indices[0]:
        venue_id = int(venue_data.iloc[idx]['id'])
        if venue_id == venue.id:
            continue
        
        venue_lat = venue_data.iloc[idx]['lat']
        venue_lng = venue_data.iloc[idx]['lng']
        distance = haversine(ref_lng, ref_lat, venue_lng, venue_lat)
        
        if distance <= max_distance_km * 2: 
            price_match_venues.append((venue_id, distance))
    
    price_match_venues = sorted(price_match_venues, key=lambda x: x[1])[:n_recommendations]
    price_match_venue_ids = [v[0] for v in price_match_venues]
    
    # Fetch venue objects (assuming VenueModel is defined and accessible)
    similar = VenueModel.objects.filter(id__in=similar_venue_ids) if similar_venue_ids else VenueModel.objects.none()
    same_location = VenueModel.objects.filter(id__in=same_location_venue_ids) if same_location_venue_ids else VenueModel.objects.none()
    price_match = VenueModel.objects.filter(id__in=price_match_venue_ids) if price_match_venue_ids else VenueModel.objects.none()
    
    # Preserve order
    similar = sorted(similar, key=lambda x: similar_venue_ids.index(x.id))
    same_location = sorted(same_location, key=lambda x: same_location_venue_ids.index(x.id))
    price_match = sorted(price_match, key=lambda x: price_match_venue_ids.index(x.id))

    return {
        "similar": similar,
        "same_location": same_location,
        "price_match": price_match,
    }