import socketio
import eventlet
from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

# Create Flask app for Socket.IO
app = Flask(__name__)
CORS(app)

# Initialize Socket.IO server
sio = socketio.Server(cors_allowed_origins="*")

# Wrap Flask app with Socket.IO
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Store active deliveries and their connected clients
active_deliveries = {}
delivery_clients = {}

@sio.event
def connect(sid, environ):
    """Handle client connection"""
    print(f'Client {sid} connected')
    sio.emit('connected', {'message': 'Connected to delivery tracking server'}, room=sid)

@sio.event
def disconnect(sid):
    """Handle client disconnection"""
    print(f'Client {sid} disconnected')
    
    # Remove client from all delivery rooms
    for delivery_id, clients in delivery_clients.items():
        if sid in clients:
            clients.remove(sid)
            if not clients:
                del delivery_clients[delivery_id]

@sio.event
def join_delivery(sid, data):
    """Join a specific delivery for real-time updates"""
    try:
        delivery_id = data.get('delivery_id')
        if not delivery_id:
            sio.emit('error', {'message': 'delivery_id is required'}, room=sid)
            return
        
        # Add client to delivery room
        if delivery_id not in delivery_clients:
            delivery_clients[delivery_id] = []
        
        if sid not in delivery_clients[delivery_id]:
            delivery_clients[delivery_id].append(sid)
        
        sio.enter_room(sid, f'delivery_{delivery_id}')
        sio.emit('joined_delivery', {
            'delivery_id': delivery_id,
            'message': f'Joined delivery tracking for {delivery_id}'
        }, room=sid)
        
        print(f'Client {sid} joined delivery {delivery_id}')
        
    except Exception as e:
        sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
def leave_delivery(sid, data):
    """Leave a specific delivery"""
    try:
        delivery_id = data.get('delivery_id')
        if delivery_id:
            sio.leave_room(sid, f'delivery_{delivery_id}')
            
            # Remove from delivery clients
            if delivery_id in delivery_clients and sid in delivery_clients[delivery_id]:
                delivery_clients[delivery_id].remove(sid)
            
            sio.emit('left_delivery', {
                'delivery_id': delivery_id,
                'message': f'Left delivery tracking for {delivery_id}'
            }, room=sid)
            
            print(f'Client {sid} left delivery {delivery_id}')
        
    except Exception as e:
        sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
def update_location(sid, data):
    """Handle location updates from delivery agents"""
    try:
        delivery_id = data.get('delivery_id')
        location = data.get('location')
        
        if not delivery_id or not location:
            sio.emit('error', {'message': 'delivery_id and location are required'}, room=sid)
            return
        
        # Store location update
        active_deliveries[delivery_id] = {
            'location': location,
            'timestamp': data.get('timestamp'),
            'agent_id': sid
        }
        
        # Broadcast to all clients tracking this delivery
        sio.emit('location_update', {
            'delivery_id': delivery_id,
            'location': location,
            'timestamp': data.get('timestamp')
        }, room=f'delivery_{delivery_id}')
        
        print(f'Location updated for delivery {delivery_id}: {location}')
        
    except Exception as e:
        sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
def stop_completed(sid, data):
    """Handle stop completion updates"""
    try:
        delivery_id = data.get('delivery_id')
        stop_index = data.get('stop_index')
        
        if not delivery_id or stop_index is None:
            sio.emit('error', {'message': 'delivery_id and stop_index are required'}, room=sid)
            return
        
        # Broadcast stop completion to all clients
        sio.emit('stop_completed', {
            'delivery_id': delivery_id,
            'stop_index': stop_index,
            'timestamp': data.get('timestamp')
        }, room=f'delivery_{delivery_id}')
        
        print(f'Stop {stop_index} completed for delivery {delivery_id}')
        
    except Exception as e:
        sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
def delivery_completed(sid, data):
    """Handle delivery completion"""
    try:
        delivery_id = data.get('delivery_id')
        
        if not delivery_id:
            sio.emit('error', {'message': 'delivery_id is required'}, room=sid)
            return
        
        # Broadcast delivery completion
        sio.emit('delivery_completed', {
            'delivery_id': delivery_id,
            'timestamp': data.get('timestamp')
        }, room=f'delivery_{delivery_id}')
        
        # Clean up active delivery
        if delivery_id in active_deliveries:
            del active_deliveries[delivery_id]
        
        print(f'Delivery {delivery_id} completed')
        
    except Exception as e:
        sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
def get_delivery_status(sid, data):
    """Get current status of a delivery"""
    try:
        delivery_id = data.get('delivery_id')
        
        if not delivery_id:
            sio.emit('error', {'message': 'delivery_id is required'}, room=sid)
            return
        
        if delivery_id in active_deliveries:
            sio.emit('delivery_status', {
                'delivery_id': delivery_id,
                'status': 'active',
                'current_location': active_deliveries[delivery_id]['location'],
                'last_update': active_deliveries[delivery_id]['timestamp']
            }, room=sid)
        else:
            sio.emit('delivery_status', {
                'delivery_id': delivery_id,
                'status': 'inactive',
                'message': 'Delivery not found or not active'
            }, room=sid)
        
    except Exception as e:
        sio.emit('error', {'message': str(e)}, room=sid)

# Utility functions for external use
def broadcast_location_update(delivery_id, location, timestamp=None):
    """Broadcast location update to all clients tracking a delivery"""
    sio.emit('location_update', {
        'delivery_id': delivery_id,
        'location': location,
        'timestamp': timestamp
    }, room=f'delivery_{delivery_id}')

def broadcast_stop_completion(delivery_id, stop_index, timestamp=None):
    """Broadcast stop completion to all clients"""
    sio.emit('stop_completed', {
        'delivery_id': delivery_id,
        'stop_index': stop_index,
        'timestamp': timestamp
    }, room=f'delivery_{delivery_id}')

def broadcast_delivery_completion(delivery_id, timestamp=None):
    """Broadcast delivery completion to all clients"""
    sio.emit('delivery_completed', {
        'delivery_id': delivery_id,
        'timestamp': timestamp
    }, room=f'delivery_{delivery_id}')

if __name__ == '__main__':
    port = int(os.environ.get('SOCKETIO_PORT', 5001))
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port)), app)
