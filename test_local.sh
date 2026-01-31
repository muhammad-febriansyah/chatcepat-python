#!/bin/bash

# Script untuk testing Google Maps Scraper API di local

echo "🧪 Testing Google Maps Scraper API"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API is running
echo "📡 Checking if API is running..."
HEALTH_CHECK=$(curl -s http://localhost:5000/health)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API is running${NC}"
    echo "Response: $HEALTH_CHECK"
    echo ""
else
    echo -e "${RED}✗ API is not running${NC}"
    echo "Please start the API first: python3 api.py"
    exit 1
fi

# Test scraping
echo "🔍 Testing scraping endpoint..."
echo "Query: restaurant di Menteng, Jakarta (max 3 results)"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: chatcepat-secret-key-2024" \
  -d '{
    "keyword": "restaurant",
    "location": "Jakarta",
    "kecamatan": "Menteng",
    "max_results": 3
  }')

# Check if successful
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ Scraping successful${NC}"
    echo ""

    # Parse response
    TOTAL=$(echo "$RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')
    METHOD=$(echo "$RESPONSE" | grep -o '"method":"[^"]*"' | cut -d'"' -f4)

    echo "Method: $METHOD"
    echo "Total results: $TOTAL"
    echo ""
    echo "Full response:"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ Scraping failed${NC}"
    echo "Response: $RESPONSE"
fi

echo ""
echo "=================================="
echo "Test completed!"
