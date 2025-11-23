import os
import joblib
from scipy.sparse import hstack, csr_matrix
from django.conf import settings
from apps.venue.models import VenueModel

# Load models once
MODEL_DIR = settings.KNN_MODEL_DIR

knn = joblib.load(os.path.join(MODEL_DIR, "knn_venues.pkl"))
ohe = joblib.load(os.path.join(MODEL_DIR, "ohe_venues.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler_venues.pkl"))
venue_data = joblib.load(os.path.join(MODEL_DIR, "venue_data.pkl"))

def recommend_venues(venue_id, n_recommendations=5):
    # Check if venue exists
    venue_row = venue_data[venue_data["id"] == venue_id]
    if venue_row.empty:
        return {
            "similar": VenueModel.objects.none(),
            "same_location": VenueModel.objects.none(),
            "price_match": VenueModel.objects.none(),
        }

    venue_row = venue_row.iloc[0]

    # Transform KNN features
    city_vector = csr_matrix(ohe.transform([[venue_row["city_id"]]]))
    price_vector = csr_matrix(scaler.transform([[venue_row["veg_price"], venue_row["non_veg_price"]]]))
    combined_features = hstack([city_vector, price_vector])

    # ---- 1. Similar venues using KNN ----
    distances, indices = knn.kneighbors(combined_features, n_neighbors=n_recommendations + 1)
    similar_ids = venue_data.iloc[indices[0][1:]]["id"].tolist()  # exclude self
    similar_venues = VenueModel.objects.filter(id__in=similar_ids)

    # ---- 2. Same location venues ----
    same_location_venues = VenueModel.objects.filter(city_id=venue_row["city_id"]).exclude(id=venue_id)[:n_recommendations]

    # ---- 3. Similar veg/non-veg price venues ----
    price_tolerance = 0.2  # 20% price range
    veg_min = venue_row["veg_price"] * (1 - price_tolerance)
    veg_max = venue_row["veg_price"] * (1 + price_tolerance)
    nonveg_min = venue_row["non_veg_price"] * (1 - price_tolerance)
    nonveg_max = venue_row["non_veg_price"] * (1 + price_tolerance)

    price_match_venues = VenueModel.objects.filter(
        veg_price__gte=veg_min, veg_price__lte=veg_max,
        non_veg_price__gte=nonveg_min, non_veg_price__lte=nonveg_max
    ).exclude(id=venue_id)[:n_recommendations]

    return {
        "similar": similar_venues,
        "same_location": same_location_venues,
        "price_match": price_match_venues
    }
