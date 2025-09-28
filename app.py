from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime
from db.models import RouteModel, DeliveryModel
from optimization.tsp import RouteOptimizer
from geocoding.geocoder import GeocodingService
import socketio

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Socket.IO server
sio = socketio.Server(cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Initialize services
route_optimizer = RouteOptimizer()
geocoding_service = GeocodingService()

# Initialize database models
route_model = RouteModel()
delivery_model = DeliveryModel()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'route-optimization-ms',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/optimize-route', methods=['POST'])
def optimize_route():
    """Optimize delivery route for given addresses"""
    try:
        data = request.get_json()
        
        if not data or 'addresses' not in data:
            return jsonify({'error': 'Addresses are required'}), 400
        
        addresses = data['addresses']
        start_location = data.get('start_location', '')
        
        if not addresses or len(addresses) < 2:
            return jsonify({'error': 'At least 2 addresses are required'}), 400
        
        # Generate unique route ID
        route_id = str(uuid.uuid4())
        
        # Geocode addresses to coordinates
        coordinates = []
        for address in addresses:
            coord = geocoding_service.geocode_address(address)
            if coord:
                coordinates.append({
                    'address': address,
                    'latitude': coord['lat'],
                    'longitude': coord['lng']
                })
            else:
                return jsonify({'error': f'Could not geocode address: {address}'}), 400
        
        # Add start location if provided
        start_coord = None
        if start_location:
            start_coord = geocoding_service.geocode_address(start_location)
            if not start_coord:
                return jsonify({'error': f'Could not geocode start location: {start_location}'}), 400
        
        # Optimize route using TSP
        optimized_route = route_optimizer.optimize_route(coordinates, start_coord)
        
        # Calculate total distance and estimated time
        total_distance = route_optimizer.calculate_total_distance(optimized_route)
        estimated_time = route_optimizer.estimate_delivery_time(total_distance, len(addresses))
        
        # Create route object
        route_data = {
            'route_id': route_id,
            'addresses': optimized_route,
            'total_distance': total_distance,
            'estimated_time': estimated_time,
            'created_at': datetime.utcnow(),
            'status': 'optimized'
        }
        
        # Save to database
        route_model.create_route(route_data)
        
        return jsonify({
            'route_id': route_id,
            'optimized_route': optimized_route,
            'total_distance': total_distance,
            'estimated_time': estimated_time,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/route/<route_id>', methods=['GET'])
def get_route(route_id):
    """Get route details by ID"""
    try:
        route = route_model.get_route(route_id)
        if not route:
            return jsonify({'error': 'Route not found'}), 404
        
        return jsonify(route)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/route/<route_id>/start', methods=['POST'])
def start_delivery(route_id):
    """Start delivery for a route"""
    try:
        route = route_model.get_route(route_id)
        if not route:
            return jsonify({'error': 'Route not found'}), 404
        
        # Create delivery tracking record
        delivery_data = {
            'delivery_id': str(uuid.uuid4()),
            'route_id': route_id,
            'status': 'in_progress',
            'started_at': datetime.utcnow(),
            'current_location': None,
            'completed_stops': []
        }
        
        delivery_model.create_delivery(delivery_data)
        
        # Update route status
        route_model.update_route_status(route_id, 'in_progress')
        
        return jsonify({
            'delivery_id': delivery_data['delivery_id'],
            'status': 'started',
            'message': 'Delivery tracking started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/track/update', methods=['POST'])
def update_location():
    """Update delivery agent location for real-time tracking"""
    try:
        data = request.get_json()
        
        if not data or 'delivery_id' not in data or 'location' not in data:
            return jsonify({'error': 'delivery_id and location are required'}), 400
        
        delivery_id = data['delivery_id']
        location = data['location']
        
        # Update delivery location in database
        delivery_model.update_location(delivery_id, location)
        
        # Emit real-time update to connected clients
        sio.emit('location-update', {
            'delivery_id': delivery_id,
            'location': location,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({'status': 'updated'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delivery/<delivery_id>/complete-stop', methods=['POST'])
def complete_stop(delivery_id):
    """Mark a delivery stop as completed"""
    try:
        data = request.get_json()
        stop_index = data.get('stop_index')
        
        if stop_index is None:
            return jsonify({'error': 'stop_index is required'}), 400
        
        # Update delivery with completed stop
        delivery_model.complete_stop(delivery_id, stop_index)
        
        # Emit completion update
        sio.emit('stop-completed', {
            'delivery_id': delivery_id,
            'stop_index': stop_index,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({'status': 'stop_completed'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delivery/<delivery_id>/complete', methods=['POST'])
def complete_delivery(delivery_id):
    """Mark entire delivery as completed"""
    try:
        # Update delivery status
        delivery_model.complete_delivery(delivery_id)
        
        # Get delivery details
        delivery = delivery_model.get_delivery(delivery_id)
        if delivery:
            # Update route status
            route_model.update_route_status(delivery['route_id'], 'completed')
            
            # Emit completion update
            sio.emit('delivery-completed', {
                'delivery_id': delivery_id,
                'route_id': delivery['route_id'],
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return jsonify({'status': 'delivery_completed'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Socket.IO event handlers
@sio.event
def connect(sid, environ):
    print(f'Client {sid} connected')

@sio.event
def disconnect(sid):
    print(f'Client {sid} disconnected')

@sio.event
def join_delivery(sid, data):
    """Join a specific delivery for real-time updates"""
    delivery_id = data.get('delivery_id')
    if delivery_id:
        sio.enter_room(sid, f'delivery_{delivery_id}')
        sio.emit('joined_delivery', {'delivery_id': delivery_id}, room=sid)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
