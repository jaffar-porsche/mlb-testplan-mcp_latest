#!/usr/bin/env python3
"""
Simple Confluence MCP Server Test Script

Demonstrates basic usage of the Confluence MCP server with example data.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8001"
EXAMPLE_SPACE_KEY = "TEST"  # Change this to a valid space key in your Confluence

def test_api_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint and return the result."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, str(e)

def main():
    print("🧪 Confluence MCP Server - Simple Test Script")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("\n1. Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running!")
        print("💡 Run: ./start-mcp.sh or start-mcp.bat")
        return
    
    # Test 1.5: Test Confluence connection
    print("\n1.5. Testing Confluence connection...")
    success, result = test_api_endpoint("GET", "/test_connection")
    if success:
        if result.get('status') == 'connected':
            print(f"✅ Connected to Confluence as: {result.get('user', 'Unknown')}")
        else:
            print(f"❌ Confluence connection failed: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Could not test connection: {result}")
    
    # Test 2: List spaces
    print("\n2. Testing list spaces...")
    success, result = test_api_endpoint("GET", "/spaces")
    if success:
        print(f"✅ Found {result.get('total', 0)} spaces")
        if result.get('spaces'):
            print("   Available spaces:")
            for space in result['spaces'][:3]:  # Show first 3
                print(f"   - {space['key']}: {space['name']}")
    else:
        print(f"❌ Failed: {result}")
    
    # Test 3: Search content
    print("\n3. Testing search...")
    success, result = test_api_endpoint("GET", "/search", params={"query": "test", "limit": 5})
    if success:
        print(f"✅ Search returned {result.get('total', 0)} results")
        if result.get('results'):
            print("   Sample results:")
            for res in result['results'][:2]:  # Show first 2
                print(f"   - {res.get('title', 'No title')}")
    else:
        print(f"❌ CQL search failed: {result}")
        print("💡 Trying simple search in TEST space...")
        # Try simple search as fallback
        success, result = test_api_endpoint("GET", "/search_simple", params={"space_key": EXAMPLE_SPACE_KEY, "query": "test", "limit": 5})
        if success:
            print(f"✅ Simple search returned {result.get('total', 0)} results")
        else:
            print(f"❌ Simple search also failed: {result}")
    
    # Test 4: Create a test page (if we have a valid space)
    print(f"\n4. Testing page creation in space '{EXAMPLE_SPACE_KEY}'...")
    test_page_data = {
        "space_key": EXAMPLE_SPACE_KEY,
        "title": f"Test Page - {int(time.time())}",
        "body": "<h1>Test Page</h1><p>This is a test page created by the MCP test client.</p><p>Created at: " + time.strftime("%Y-%m-%d %H:%M:%S") + "</p>"
    }
    
    success, result = test_api_endpoint("POST", "/create_page", data=test_page_data)
    if success:
        page_id = result['id']
        print(f"✅ Created page: {result['title']}")
        print(f"   Page ID: {page_id}")
        print(f"   URL: {result['url']}")
    else:
        print(f"❌ Regular create failed: {result}")
        print("💡 Trying simplified create method...")
        
        # Try simplified create
        success, result = test_api_endpoint("POST", "/create_page_simple", data=test_page_data)
        if success:
            page_id = result['id']
            print(f"✅ Created page with simplified method: {result['title']}")
            print(f"   Page ID: {page_id}")
            print(f"   URL: {result['url']}")
        else:
            print(f"❌ Simplified create also failed: {result}")
            print(f"💡 Make sure space '{EXAMPLE_SPACE_KEY}' exists and you have write permissions")
            page_id = None
    
    if page_id:
        
        # Test 5: Get the created page
        print(f"\n5. Testing get page {page_id}...")
        success, result = test_api_endpoint("GET", f"/page/{page_id}")
        if success:
            print(f"✅ Retrieved page: {result['title']}")
            print(f"   Version: {result['version']}")
        else:
            print(f"❌ Failed: {result}")
        
        # Test 6: Update the page
        print(f"\n6. Testing page update...")
        update_data = {
            "body": "<h1>Updated Test Page</h1><p>This page has been updated by the test client.</p><p>Updated at: " + time.strftime("%Y-%m-%d %H:%M:%S") + "</p>"
        }
        success, result = test_api_endpoint("PUT", f"/page/{page_id}", data=update_data)
        if success:
            print(f"✅ Updated page to version {result['version']}")
        else:
            print(f"❌ Failed: {result}")
    else:
        print(f"❌ Failed to create page: {result}")
        print(f"💡 Make sure space '{EXAMPLE_SPACE_KEY}' exists or change EXAMPLE_SPACE_KEY in the script")
    
    print("\n🎉 Test completed!")
    print("\n💡 For interactive testing, run: python test_client.py")

if __name__ == "__main__":
    main()
