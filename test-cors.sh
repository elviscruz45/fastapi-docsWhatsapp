#!/bin/bash

echo "🧪 Testing CORS configuration on Google Cloud API..."

# Test 1: OPTIONS preflight request
echo ""
echo "=== Test 1: OPTIONS preflight request ==="
curl -X OPTIONS \
  -H "Origin: https://platform.minetrack.site" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v \
  https://api.minetrack.site/crear-informe-final

echo ""
echo "=== Test 2: GET request with CORS headers ==="
curl -X GET \
  -H "Origin: https://platform.minetrack.site" \
  -v \
  https://api.minetrack.site/test-cors

echo ""
echo "=== Test 3: Check main endpoint ==="
curl -X GET \
  -H "Origin: https://platform.minetrack.site" \
  -v \
  https://api.minetrack.site/

echo ""
echo "🔍 Expected CORS headers in response:"
echo "  - Access-Control-Allow-Origin: https://platform.minetrack.site"
echo "  - Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS"
echo "  - Access-Control-Allow-Headers: *"
echo "  - Access-Control-Allow-Credentials: true"