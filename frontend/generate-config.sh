#!/bin/sh

DEFAULT_API_URL="http://localhost:8000"

API_URL="${VITE_API_URL:-$DEFAULT_API_URL}"

echo "🔧 Generating runtime configuration..."
echo "📡 API URL: $API_URL"

mkdir -p /app/dist

cat > /app/dist/config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_URL: '$API_URL'
};
console.log('🚀 Runtime config loaded:', window.__RUNTIME_CONFIG__);
EOF

echo "✅ Runtime configuration generated successfully!"
echo "📄 Config file contents:"
cat /app/dist/config.js
