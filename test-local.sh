#!/bin/bash

echo "🧪 Testing local deployment..."

echo "🔍 Testing backend health..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/api/v1/health/health)
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is not healthy"
    echo "$BACKEND_HEALTH"
    exit 1
fi

echo "🔍 Testing frontend configuration..."
FRONTEND_CONFIG=$(curl -s http://localhost:3000/config.js)
if echo "$FRONTEND_CONFIG" | grep -q "http://localhost:8000"; then
    echo "✅ Frontend configuration is correct"
else
    echo "❌ Frontend configuration is incorrect"
    echo "$FRONTEND_CONFIG"
    exit 1
fi

echo "🔍 Testing frontend is serving..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo "✅ Frontend is serving correctly"
else
    echo "❌ Frontend is not serving correctly (HTTP $FRONTEND_RESPONSE)"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Ready for AWS deployment."
echo "🚀 Run './deploy-aws.sh' to deploy to AWS"
