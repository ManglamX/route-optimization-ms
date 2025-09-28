from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import os as _os

# Load .env from the microservice root (one level up from this db/ folder) when present.
# This makes the connection robust even if the process is started from a different cwd.
_env_path = _os.path.join(_os.path.dirname(__file__), '..', '.env')
if _os.path.exists(_env_path):
    print(f"Loading environment from: {_env_path}")
    load_dotenv(_env_path)
else:
    # Fall back to the default search behavior
    print("No .env found at microservice root, loading from default locations")
    load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb+srv://ManglamX:Manglam%40529@nourishnet.bjjeltx.mongodb.net/NourishNet')
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client.nourishnet_routes
            # Test connection
            self.client.admin.command('ping')
            self.connected = True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print("Running in mock mode - data will not be persisted")
            self.client = None
            self.db = None
            self.connected = False
    
    def get_collection(self, collection_name):
        if self.connected:
            return self.db[collection_name]
        return None

# Initialize database connection
db_connection = DatabaseConnection()

class RouteModel:
    def __init__(self):
        self.collection = db_connection.get_collection('routes')
        self.mock_data = {}  # Store data in memory when MongoDB is not available
    
    def create_route(self, route_data):
        """Create a new route in the database"""
        try:
            if self.collection:
                result = self.collection.insert_one(route_data)
                return str(result.inserted_id)
            else:
                # Mock mode - store in memory
                route_id = route_data.get('route_id', 'mock_route_id')
                self.mock_data[route_id] = route_data
                return route_id
        except Exception as e:
            print(f"Error creating route: {e}")
            return None
    
    def get_route(self, route_id):
        """Get route by ID"""
        try:
            if self.collection:
                route = self.collection.find_one({'route_id': route_id})
                if route:
                    route['_id'] = str(route['_id'])
                return route
            else:
                # Mock mode
                return self.mock_data.get(route_id)
        except Exception as e:
            print(f"Error getting route: {e}")
            return None
    
    def update_route_status(self, route_id, status):
        """Update route status"""
        try:
            if self.collection:
                result = self.collection.update_one(
                    {'route_id': route_id},
                    {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
                )
                return result.modified_count > 0
            else:
                # Mock mode
                if route_id in self.mock_data:
                    self.mock_data[route_id]['status'] = status
                    self.mock_data[route_id]['updated_at'] = datetime.utcnow()
                    return True
                return False
        except Exception as e:
            print(f"Error updating route status: {e}")
            return False
    
    def get_routes_by_status(self, status):
        """Get all routes by status"""
        try:
            if self.collection:
                routes = list(self.collection.find({'status': status}))
                for route in routes:
                    route['_id'] = str(route['_id'])
                return routes
            else:
                # Mock mode
                return [route for route in self.mock_data.values() if route.get('status') == status]
        except Exception as e:
            print(f"Error getting routes by status: {e}")
            return []
    
    def delete_route(self, route_id):
        """Delete a route"""
        try:
            if self.collection:
                result = self.collection.delete_one({'route_id': route_id})
                return result.deleted_count > 0
            else:
                # Mock mode
                if route_id in self.mock_data:
                    del self.mock_data[route_id]
                    return True
                return False
        except Exception as e:
            print(f"Error deleting route: {e}")
            return False

class DeliveryModel:
    def __init__(self):
        self.collection = db_connection.get_collection('deliveries')
        self.mock_data = {}  # Store data in memory when MongoDB is not available
    
    def create_delivery(self, delivery_data):
        """Create a new delivery tracking record"""
        try:
            if self.collection:
                result = self.collection.insert_one(delivery_data)
                return str(result.inserted_id)
            else:
                # Mock mode
                delivery_id = delivery_data.get('delivery_id', 'mock_delivery_id')
                self.mock_data[delivery_id] = delivery_data
                return delivery_id
        except Exception as e:
            print(f"Error creating delivery: {e}")
            return None
    
    def get_delivery(self, delivery_id):
        """Get delivery by ID"""
        try:
            if self.collection:
                delivery = self.collection.find_one({'delivery_id': delivery_id})
                if delivery:
                    delivery['_id'] = str(delivery['_id'])
                return delivery
            else:
                # Mock mode
                return self.mock_data.get(delivery_id)
        except Exception as e:
            print(f"Error getting delivery: {e}")
            return None
    
    def update_location(self, delivery_id, location):
        """Update delivery agent location"""
        try:
            if self.collection:
                result = self.collection.update_one(
                    {'delivery_id': delivery_id},
                    {'$set': {
                        'current_location': location,
                        'last_location_update': datetime.utcnow()
                    }}
                )
                return result.modified_count > 0
            else:
                # Mock mode
                if delivery_id in self.mock_data:
                    self.mock_data[delivery_id]['current_location'] = location
                    self.mock_data[delivery_id]['last_location_update'] = datetime.utcnow()
                    return True
                return False
        except Exception as e:
            print(f"Error updating location: {e}")
            return False
    
    def complete_stop(self, delivery_id, stop_index):
        """Mark a delivery stop as completed"""
        try:
            if self.collection:
                result = self.collection.update_one(
                    {'delivery_id': delivery_id},
                    {
                        '$addToSet': {'completed_stops': stop_index},
                        '$set': {'last_stop_completed': datetime.utcnow()}
                    }
                )
                return result.modified_count > 0
            else:
                # Mock mode
                if delivery_id in self.mock_data:
                    if 'completed_stops' not in self.mock_data[delivery_id]:
                        self.mock_data[delivery_id]['completed_stops'] = []
                    if stop_index not in self.mock_data[delivery_id]['completed_stops']:
                        self.mock_data[delivery_id]['completed_stops'].append(stop_index)
                    self.mock_data[delivery_id]['last_stop_completed'] = datetime.utcnow()
                    return True
                return False
        except Exception as e:
            print(f"Error completing stop: {e}")
            return False
    
    def complete_delivery(self, delivery_id):
        """Mark entire delivery as completed"""
        try:
            if self.collection:
                result = self.collection.update_one(
                    {'delivery_id': delivery_id},
                    {
                        '$set': {
                            'status': 'completed',
                            'completed_at': datetime.utcnow()
                        }
                    }
                )
                return result.modified_count > 0
            else:
                # Mock mode
                if delivery_id in self.mock_data:
                    self.mock_data[delivery_id]['status'] = 'completed'
                    self.mock_data[delivery_id]['completed_at'] = datetime.utcnow()
                    return True
                return False
        except Exception as e:
            print(f"Error completing delivery: {e}")
            return False
    
    def get_active_deliveries(self):
        """Get all active deliveries"""
        try:
            if self.collection:
                deliveries = list(self.collection.find({'status': 'in_progress'}))
                for delivery in deliveries:
                    delivery['_id'] = str(delivery['_id'])
                return deliveries
            else:
                # Mock mode
                return [delivery for delivery in self.mock_data.values() if delivery.get('status') == 'in_progress']
        except Exception as e:
            print(f"Error getting active deliveries: {e}")
            return []
    
    def get_delivery_by_route(self, route_id):
        """Get delivery by route ID"""
        try:
            if self.collection:
                delivery = self.collection.find_one({'route_id': route_id})
                if delivery:
                    delivery['_id'] = str(delivery['_id'])
                return delivery
            else:
                # Mock mode
                for delivery in self.mock_data.values():
                    if delivery.get('route_id') == route_id:
                        return delivery
                return None
        except Exception as e:
            print(f"Error getting delivery by route: {e}")
            return None
