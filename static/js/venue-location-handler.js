// Location handler for venue pages
// Add this to your base template or venue detail template

(function() {
    'use strict';
    
    const LocationHandler = {
        STORAGE_KEY: 'user_location',
        CACHE_DURATION: 5 * 60 * 1000, // 5 minutes in milliseconds
        
        /**
         * Get cached location from sessionStorage
         */
        getCachedLocation() {
            try {
                const cached = sessionStorage.getItem(this.STORAGE_KEY);
                if (!cached) return null;
                
                const data = JSON.parse(cached);
                const now = Date.now();
                
                // Check if cache is still valid
                if (now - data.timestamp < this.CACHE_DURATION) {
                    return { lat: data.lat, lng: data.lng };
                }
                
                // Cache expired
                sessionStorage.removeItem(this.STORAGE_KEY);
                return null;
            } catch (e) {
                console.error('Error reading cached location:', e);
                return null;
            }
        },
        
        /**
         * Cache location to sessionStorage
         */
        cacheLocation(lat, lng) {
            try {
                const data = {
                    lat: lat,
                    lng: lng,
                    timestamp: Date.now()
                };
                sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
            } catch (e) {
                console.error('Error caching location:', e);
            }
        },
        
        /**
         * Get user's current location with improved settings
         */
        async getCurrentLocation() {
            // Check cache first
            const cached = this.getCachedLocation();
            if (cached) {
                console.log('Using cached location');
                return cached;
            }
            
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation not supported'));
                    return;
                }
                
                // Try with high accuracy first, but with longer timeout
                const options = {
                    enableHighAccuracy: true,
                    timeout: 30000, // Increased to 30 seconds
                    maximumAge: 0 // Don't use cached positions from browser
                };
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const location = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude
                        };
                        
                        // Cache the location
                        this.cacheLocation(location.lat, location.lng);
                        resolve(location);
                    },
                    (error) => {
                        console.warn('High accuracy geolocation failed, trying low accuracy...', error);
                        
                        // If high accuracy fails, try with low accuracy (faster but less precise)
                        const lowAccuracyOptions = {
                            enableHighAccuracy: false,
                            timeout: 20000, // 20 seconds for low accuracy
                            maximumAge: 300000 // Accept cached positions up to 5 minutes old
                        };
                        
                        navigator.geolocation.getCurrentPosition(
                            (position) => {
                                const location = {
                                    lat: position.coords.latitude,
                                    lng: position.coords.longitude
                                };
                                
                                this.cacheLocation(location.lat, location.lng);
                                resolve(location);
                            },
                            (lowAccError) => {
                                console.error('Geolocation error:', lowAccError);
                                reject(this.getReadableError(lowAccError));
                            },
                            lowAccuracyOptions
                        );
                    },
                    options
                );
            });
        },
        
        /**
         * Convert geolocation error to readable message
         */
        getReadableError(error) {
            let message = 'Unable to get your location';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    message = 'Location permission denied. Please enable location in your browser settings.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    message = 'Location information unavailable. Please check your GPS/internet connection.';
                    break;
                case error.TIMEOUT:
                    message = 'Location request timed out. Please try again or check your connection.';
                    break;
                default:
                    message = 'An unknown error occurred while getting location.';
            }
            
            return new Error(message);
        },
        
        /**
         * Send location to Django backend via AJAX
         */
        async sendLocationToBackend(lat, lng) {
            try {
                const response = await fetch('/api/store-location/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({ lat, lng })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to store location');
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error sending location to backend:', error);
                throw error;
            }
        },
        
        /**
         * Reload page with location parameters
         */
        reloadWithLocation(lat, lng) {
            const url = new URL(window.location.href);
            url.searchParams.set('lat', lat);
            url.searchParams.set('lng', lng);
            window.location.href = url.toString();
        },
        
        /**
         * Get CSRF token from cookie
         */
        getCSRFToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },
        
        /**
         * Show location permission prompt
         */
        showLocationPrompt() {
            const prompt = document.getElementById('location-prompt');
            if (prompt) {
                prompt.style.display = 'block';
            }
        },
        
        /**
         * Hide location permission prompt
         */
        hideLocationPrompt() {
            const prompt = document.getElementById('location-prompt');
            if (prompt) {
                prompt.style.display = 'none';
            }
        },
        
        /**
         * Initialize location handling
         */
        async initialize() {
            // Check if we're on a venue detail page
            const isVenuePage = document.querySelector('[data-venue-detail]') !== null;
            if (!isVenuePage) return;
            
            // Check if location is already in URL or session
            const urlParams = new URLSearchParams(window.location.search);
            const hasLocationInUrl = urlParams.has('lat') && urlParams.has('lng');
            
            if (hasLocationInUrl) {
                console.log('Location already in URL');
                return;
            }
            
            // Check for cached location
            const cached = this.getCachedLocation();
            if (cached) {
                console.log('Using cached location for recommendations');
                
                // Send to backend without reloading
                try {
                    await this.sendLocationToBackend(cached.lat, cached.lng);
                    console.log('Location sent to backend');
                } catch (e) {
                    console.error('Failed to send location to backend:', e);
                }
                return;
            }
            
            // Show prompt to user
            this.showLocationPrompt();
        },
        
        /**
         * Request location permission and process
         */
        async requestLocationPermission() {
            try {
                this.hideLocationPrompt();
                
                // Show loading indicator
                const loadingEl = document.getElementById('location-loading');
                if (loadingEl) loadingEl.style.display = 'block';
                
                // Get location (with improved error handling)
                const location = await this.getCurrentLocation();
                
                // Send to backend
                await this.sendLocationToBackend(location.lat, location.lng);
                
                // Reload page with location for better recommendations
                this.reloadWithLocation(location.lat, location.lng);
                
            } catch (error) {
                console.error('Location permission error:', error);
                
                // Hide loading
                const loadingEl = document.getElementById('location-loading');
                if (loadingEl) loadingEl.style.display = 'none';
                
                // Show error message
                const errorEl = document.getElementById('location-error');
                if (errorEl) {
                    errorEl.textContent = error.message || 'Unable to get your location. Showing general recommendations.';
                    errorEl.style.display = 'block';
                    
                    setTimeout(() => {
                        errorEl.style.display = 'none';
                    }, 8000);
                }
                
                // Still hide the prompt even on error
                this.hideLocationPrompt();
            }
        }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            LocationHandler.initialize();
        });
    } else {
        LocationHandler.initialize();
    }
    
    // Expose to global scope for button clicks
    window.VenueLocationHandler = LocationHandler;
    
})();