#!/bin/bash

set -e

echo "🚀 Starting AWS deployment..."

cd infrastructure

if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not found. Please install it first:"
    echo "npm install -g aws-cdk"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🏗️ Bootstrapping CDK..."
cdk bootstrap

echo "🚀 Deploying stack..."
cdk deploy --require-approval never

echo "📋 Getting deployment outputs..."
FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name StoriRagStack \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendURL'].OutputValue" \
  --output text)

BACKEND_URL=$(aws cloudformation describe-stacks \
  --stack-name StoriRagStack \
  --query "Stacks[0].Outputs[?OutputKey=='BackendURL'].OutputValue" \
  --output text)

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo ""
echo "🔍 You can check the health status at: $FRONTEND_URL/health"
echo ""

deactivate

cd ..
