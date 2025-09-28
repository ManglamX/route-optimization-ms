import requests
import os
from dotenv import load_dotenv

load_dotenv()

class GeocodingService:
    def __init__(self):
        self.google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    
    def geocode_address(self, address):
        """Convert address to coordinates using Google Maps Geocoding API"""
        try:
            if not self.google_maps_api_key:
                print("Warning: Google Maps API key not found. Using mock coordinates.")
                return self._get_mock_coordinates(address)
            
            params = {
                'address': address,
                'key': self.google_maps_api_key
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': data['results'][0]['formatted_address']
                }
            else:
                print(f"Geocoding failed for address: {address}. Status: {data['status']}")
                return self._get_mock_coordinates(address)
                
        except Exception as e:
            print(f"Geocoding error for address {address}: {e}")
            return self._get_mock_coordinates(address)
    
    def _get_mock_coordinates(self, address):
        """Generate mock coordinates for testing when API is not available"""
        # Simple hash-based mock coordinates for consistent testing
        import hashlib
        
        # Generate consistent coordinates based on address
        hash_obj = hashlib.md5(address.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert first 8 characters to coordinates
        lat_hex = hash_hex[:8]
        lng_hex = hash_hex[8:16]
        
        # Convert to latitude (19.0 to 19.2 for Mumbai area)
        lat = 19.0 + (int(lat_hex, 16) / 0xffffffff) * 0.2
        
        # Convert to longitude (72.8 to 73.0 for Mumbai area)
        lng = 72.8 + (int(lng_hex, 16) / 0xffffffff) * 0.2
        
        return {
            'lat': lat,
            'lng': lng,
            'formatted_address': f"{address} (Mock Coordinates)"
        }
    
    def reverse_geocode(self, lat, lng):
        """Convert coordinates to address using Google Maps Reverse Geocoding API"""
        try:
            if not self.google_maps_api_key:
                return f"Mock Address at {lat}, {lng}"
            
            params = {
                'latlng': f"{lat},{lng}",
                'key': self.google_maps_api_key
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                return data['results'][0]['formatted_address']
            else:
                return f"Address not found for coordinates {lat}, {lng}"
                
        except Exception as e:
            print(f"Reverse geocoding error for {lat}, {lng}: {e}")
            return f"Address not found for coordinates {lat}, {lng}"
    
    def calculate_distance_matrix(self, origins, destinations):
        """Calculate distance matrix between multiple origins and destinations"""
        try:
            if not self.google_maps_api_key:
                return self._calculate_mock_distance_matrix(origins, destinations)
            
            # Use Google Maps Distance Matrix API
            url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
            
            origins_str = '|'.join([f"{coord['lat']},{coord['lng']}" for coord in origins])
            destinations_str = '|'.join([f"{coord['lat']},{coord['lng']}" for coord in destinations])
            
            params = {
                'origins': origins_str,
                'destinations': destinations_str,
                'key': self.google_maps_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                return self._parse_distance_matrix(data)
            else:
                print(f"Distance matrix API failed: {data['status']}")
                return self._calculate_mock_distance_matrix(origins, destinations)
                
        except Exception as e:
            print(f"Distance matrix error: {e}")
            return self._calculate_mock_distance_matrix(origins, destinations)
    
    def _parse_distance_matrix(self, data):
        """Parse Google Maps Distance Matrix API response"""
        matrix = []
        for row in data['rows']:
            row_data = []
            for element in row['elements']:
                if element['status'] == 'OK':
                    distance = element['distance']['value'] / 1000  # Convert to km
                    duration = element['duration']['value'] / 60  # Convert to minutes
                    row_data.append({
                        'distance': distance,
                        'duration': duration
                    })
                else:
                    row_data.append({
                        'distance': float('inf'),
                        'duration': float('inf')
                    })
            matrix.append(row_data)
        return matrix
    
    def _calculate_mock_distance_matrix(self, origins, destinations):
        """Calculate mock distance matrix using Haversine formula"""
        import math
        
        def haversine_distance(coord1, coord2):
            lat1, lon1 = coord1['lat'], coord1['lng']
            lat2, lon2 = coord2['lat'], coord2['lng']
            
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return 6371 * c  # Earth's radius in km
        
        matrix = []
        for origin in origins:
            row = []
            for destination in destinations:
                distance = haversine_distance(origin, destination)
                duration = distance * 2.4  # Assume 25 km/h average speed
                row.append({
                    'distance': distance,
                    'duration': duration
                })
            matrix.append(row)
        
        return matrix
