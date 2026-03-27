#!/bin/bash
echo "Patent Analyzer Build Script"
echo "============================="

echo "[1/3] Installing Python dependencies..."
cd backend/backend
pip install -r requirements.txt
cd ../..

echo "[2/3] Installing React dependencies..."
cd patent-chatbot
npm install

echo "[3/3] Building React app..."
npm run build
cd ..

echo "Build complete!"