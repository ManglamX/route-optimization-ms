# Manual Testing Commands

## 1. Health Check
```bash
curl http://localhost:5000/health
```

## 2. Optimize Route
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

## 3. Get Route Details
```bash
curl http://localhost:5000/route/{route_id}
```

## 4. Start Delivery
```bash
curl -X POST http://localhost:5000/route/{route_id}/start
```

## 5. Update Location
```bash
curl -X POST http://localhost:5000/track/update \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_id": "your_delivery_id",
    "location": {
      "latitude": 19.0760,
      "longitude": 72.8777
    }
  }'
```

## 6. Complete Stop
```bash
curl -X POST http://localhost:5000/delivery/{delivery_id}/complete-stop \
  -H "Content-Type: application/json" \
  -d '{"stop_index": 0}'
```

## 7. Complete Delivery
```bash
curl -X POST http://localhost:5000/delivery/{delivery_id}/complete
```
