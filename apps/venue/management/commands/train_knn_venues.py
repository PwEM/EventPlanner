import os
import django
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import hstack, csr_matrix
import joblib
from django.conf import settings
from django.core.management.base import BaseCommand

# Initialize Django for standalone usage
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventplanner.settings")
django.setup()

from apps.venue.models import VenueModel

class Command(BaseCommand):
    help = "Train KNN venue recommendation model based on location and veg/non-veg prices"

    def handle(self, *args, **options):
        # Load all venues
        venues = VenueModel.objects.all()
        if not venues.exists():
            self.stdout.write(self.style.WARNING("No venues found in database. Exiting..."))
            return

        # Prepare dataframe
        data = pd.DataFrame(list(venues.values("id", "city_id")))
        data["veg_price"] = [v.get_veg_price or 0 for v in venues]
        data["non_veg_price"] = [v.get_non_veg_price or 0 for v in venues]

        # One-hot encode city
        ohe = OneHotEncoder(sparse_output=False)
        city_features = ohe.fit_transform(data[["city_id"]].fillna(0))

        # Scale veg and non-veg prices
        scaler = StandardScaler()
        price_features = scaler.fit_transform(data[["veg_price", "non_veg_price"]])

        # Convert to sparse matrices
        city_sparse = csr_matrix(city_features)
        price_sparse = csr_matrix(price_features)

        # Combine features
        features = hstack([city_sparse, price_sparse])

        # Train KNN
        knn = NearestNeighbors(n_neighbors=6, metric="euclidean")
        knn.fit(features)

        # Ensure model directory exists
        MODEL_DIR = getattr(settings, "KNN_MODEL_DIR", os.path.join(settings.BASE_DIR, "knn_models"))
        os.makedirs(MODEL_DIR, exist_ok=True)

        # Save models and preprocessing objects
        joblib.dump(knn, os.path.join(MODEL_DIR, "knn_venues.pkl"))
        joblib.dump(ohe, os.path.join(MODEL_DIR, "ohe_venues.pkl"))
        joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler_venues.pkl"))
        joblib.dump(data, os.path.join(MODEL_DIR, "venue_data.pkl"))

        self.stdout.write(self.style.SUCCESS(f"KNN model trained and saved in {MODEL_DIR}"))
