#!/bin/bash
# Confluence MCP Server - cURL Test Commands
# 
# Make sure the server is running before executing these commands:
# ./start-mcp.sh or start-mcp.bat

BASE_URL="http://localhost:8001"
SPACE_KEY="TEST"  # Change this to a valid space key

echo "🧪 Confluence MCP Server - cURL Test Commands"
echo "=============================================="

# Test 1: List Spaces
echo -e "\n1. List Spaces:"
curl -X GET "$BASE_URL/spaces" \
  -H "Accept: application/json" \
  | python -m json.tool

# Test 2: Search Content
echo -e "\n\n2. Search Content:"
curl -X GET "$BASE_URL/search?query=test&limit=5" \
  -H "Accept: application/json" \
  | python -m json.tool

# Test 3: Create Page
echo -e "\n\n3. Create Page:"
PAGE_RESPONSE=$(curl -X POST "$BASE_URL/create_page" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "space_key": "'$SPACE_KEY'",
    "title": "Test Page from cURL",
    "body": "<h1>Test Page</h1><p>This is a test page created via cURL.</p><p><strong>Created:</strong> '$(date)'</p>"
  }' \
  | python -m json.tool)

echo "$PAGE_RESPONSE"

# Extract page ID for subsequent tests
PAGE_ID=$(echo "$PAGE_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ ! -z "$PAGE_ID" ]; then
  echo "Page ID: $PAGE_ID"
  
  # Test 4: Get Page
  echo -e "\n\n4. Get Page Details:"
  curl -X GET "$BASE_URL/page/$PAGE_ID" \
    -H "Accept: application/json" \
    | python -m json.tool

  # Test 5: Update Page
  echo -e "\n\n5. Update Page:"
  curl -X PUT "$BASE_URL/page/$PAGE_ID" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{
      "title": "Updated Test Page from cURL",
      "body": "<h1>Updated Test Page</h1><p>This page has been updated via cURL.</p><p><strong>Updated:</strong> '$(date)'</p>"
    }' \
    | python -m json.tool
else
  echo "❌ Failed to create page or extract page ID"
fi

# Test 6: Search in Specific Space
echo -e "\n\n6. Search in Specific Space:"
curl -X GET "$BASE_URL/search?query=test&space_key=$SPACE_KEY&limit=3" \
  -H "Accept: application/json" \
  | python -m json.tool

# Test 7: Simple Search (Alternative)
echo -e "\n\n7. Simple Search in Space:"
curl -X GET "$BASE_URL/search_simple?space_key=$SPACE_KEY&query=test&limit=3" \
  -H "Accept: application/json" \
  | python -m json.tool

echo -e "\n\n✅ cURL tests completed!"
