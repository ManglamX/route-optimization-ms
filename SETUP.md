# Route Optimization Microservice - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.11+
- MongoDB (local or cloud)
- Google Maps API key (optional, will use mock data if not provided)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd route-optimization-ms

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/nourishnet_routes

# Google Maps API Configuration (optional)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Server Configuration
PORT=5000
SOCKETIO_PORT=5001
FLASK_ENV=development
```

### 4. Running the Service

#### Option A: Direct Python
```bash
# Start the main API server
python app.py

# In another terminal, start Socket.IO server
python socketio_server.py
```

#### Option B: Docker Compose
```bash
# Start all services (API + Socket.IO + MongoDB)
docker-compose up -d
```

#### Option C: Individual Docker containers
```bash
# Build the image
docker build -t nourishnet-route-ms .

# Run the container
docker run -p 5000:5000 -e MONGO_URI=mongodb://host.docker.internal:27017/nourishnet_routes nourishnet-route-ms
```

### 5. Testing the Service

```bash
# Run the test script
python test_api.py
```

## API Endpoints

### Health Check
```bash
curl http://localhost:5000/health
```

### Optimize Route
```bash
curl -X POST http://localhost:5000/optimize-route \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      "Marine Drive, Mumbai",
      "Bandra Kurla Complex, Mumbai",
      "Powai, Mumbai"
    ],
    "start_location": "Central Kitchen, Mumbai"
  }'
```

### Get Route Details
```bash
curl http://localhost:5000/route/{route_id}
```

### Start Delivery
```bash
curl -X POST http://localhost:5000/route/{route_id}/start
```

### Update Location
```bash
curl -X POST http://localhost:5000/track/update \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_id": "delivery_id_here",
    "location": {
      "latitude": 19.0760,
      "longitude": 72.8777
    }
  }'
```

## Socket.IO Integration

### JavaScript/React
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5001');

// Join delivery tracking
socket.emit('join_delivery', { delivery_id: 'your_delivery_id' });

// Listen for location updates
socket.on('location_update', (data) => {
  console.log('Location update:', data);
});

// Listen for stop completions
socket.on('stop_completed', (data) => {
  console.log('Stop completed:', data);
});
```

### React Native
```javascript
import io from 'socket.io-client';

const socket = io('http://your-server:5001');

// Same usage as above
```

## Production Deployment

### AWS EC2
1. Launch EC2 instance
2. Install Docker
3. Clone repository
4. Configure environment variables
5. Run with Docker Compose

### AWS Elastic Beanstalk
1. Create application
2. Upload as ZIP file
3. Configure environment variables
4. Deploy

### AWS Lambda + API Gateway
1. Use Zappa or Serverless Framework
2. Configure API Gateway
3. Deploy function

## Monitoring and Logs

- Health check endpoint: `/health`
- Logs are written to `logs/` directory
- MongoDB logs available in container logs

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Check MONGO_URI in .env file
   - Ensure MongoDB is running
   - Verify network connectivity

2. **Google Maps API Error**
   - Check API key validity
   - Verify billing is enabled
   - Service will fallback to mock coordinates

3. **Socket.IO Connection Issues**
   - Check CORS settings
   - Verify port 5001 is accessible
   - Ensure client and server versions match

4. **Route Optimization Fails**
   - Check OR-Tools installation
   - Verify address geocoding
   - Service will return original order as fallback

### Debug Mode
Set `FLASK_ENV=development` in .env file for detailed error messages.

## Support

For issues and questions:
1. Check the logs
2. Run the test script
3. Verify environment configuration
4. Check MongoDB connectivity
