#!/usr/bin/env python3
"""
Confluence MCP Server Test Client

A simple test client to interact with the Confluence MCP server endpoints.
Run this script to test various server functionalities.
"""

import requests
import json
import sys
from typing import Optional

class ConfluenceMCPClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_page(self, space_key: str, title: str, body: str, parent_id: Optional[str] = None) -> dict:
        """Create a new Confluence page."""
        url = f"{self.base_url}/create_page"
        data = {
            "space_key": space_key,
            "title": title,
            "body": body
        }
        if parent_id:
            data["parent_id"] = parent_id
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_page(self, page_id: str) -> dict:
        """Get details for a specific page."""
        url = f"{self.base_url}/page/{page_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def update_page(self, page_id: str, title: Optional[str] = None, body: Optional[str] = None) -> dict:
        """Update an existing page."""
        url = f"{self.base_url}/page/{page_id}"
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def search_content(self, query: str, limit: int = 10, space_key: Optional[str] = None) -> dict:
        """Search for content."""
        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "limit": limit
        }
        if space_key:
            params["space_key"] = space_key
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def list_spaces(self) -> dict:
        """List available spaces."""
        url = f"{self.base_url}/spaces"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))

def test_server_connection(client: ConfluenceMCPClient):
    """Test if the server is running."""
    try:
        response = requests.get(f"{client.base_url}/docs")
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on the correct port.")
        return False

def interactive_mode(client: ConfluenceMCPClient):
    """Interactive mode for testing the client."""
    print("\n🔧 Confluence MCP Test Client - Interactive Mode")
    print("=" * 50)
    
    while True:
        print("\nAvailable commands:")
        print("1. List spaces")
        print("2. Search content")
        print("3. Get page by ID")
        print("4. Create page")
        print("5. Update page")
        print("6. Test server connection")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        try:
            if choice == "1":
                print("\n📁 Listing spaces...")
                result = client.list_spaces()
                print_json(result)
                
            elif choice == "2":
                query = input("Enter search query: ").strip()
                limit = input("Enter limit (default 10): ").strip() or "10"
                space_key = input("Enter space key (optional): ").strip() or None
                
                print(f"\n🔍 Searching for '{query}'...")
                result = client.search_content(query, int(limit), space_key)
                print_json(result)
                
            elif choice == "3":
                page_id = input("Enter page ID: ").strip()
                print(f"\n📄 Getting page {page_id}...")
                result = client.get_page(page_id)
                print_json(result)
                
            elif choice == "4":
                space_key = input("Enter space key: ").strip()
                title = input("Enter page title: ").strip()
                print("Enter page body (HTML format):")
                print("(Type 'END' on a new line to finish)")
                body_lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    body_lines.append(line)
                body = "\n".join(body_lines)
                parent_id = input("Enter parent page ID (optional): ").strip() or None
                
                print(f"\n✨ Creating page '{title}' in space {space_key}...")
                result = client.create_page(space_key, title, body, parent_id)
                print_json(result)
                
            elif choice == "5":
                page_id = input("Enter page ID to update: ").strip()
                title = input("Enter new title (optional): ").strip() or None
                print("Enter new body (optional, type 'END' on new line to finish):")
                if input().strip():  # If user starts typing
                    body_lines = []
                    while True:
                        line = input()
                        if line.strip() == "END":
                            break
                        body_lines.append(line)
                    body = "\n".join(body_lines) if body_lines else None
                else:
                    body = None
                
                print(f"\n🔄 Updating page {page_id}...")
                result = client.update_page(page_id, title, body)
                print_json(result)
                
            elif choice == "6":
                test_server_connection(client)
                
            elif choice == "7":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def run_quick_tests(client: ConfluenceMCPClient):
    """Run a series of quick tests."""
    print("\n🧪 Running Quick Tests")
    print("=" * 30)
    
    # Test 1: List spaces
    print("\n1. Testing list spaces...")
    try:
        result = client.list_spaces()
        print(f"✅ Found {result.get('total', 0)} spaces")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Search
    print("\n2. Testing search...")
    try:
        result = client.search_content("test", limit=5)
        print(f"✅ Search returned {result.get('total', 0)} results")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n✅ Quick tests completed!")

def main():
    """Main function."""
    print("🚀 Confluence MCP Server Test Client")
    print("=" * 40)
    
    # Parse command line arguments
    base_url = "http://localhost:8001"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"📡 Connecting to: {base_url}")
    
    client = ConfluenceMCPClient(base_url)
    
    # Test server connection first
    if not test_server_connection(client):
        print("\n💡 Make sure to start the server first:")
        print("   ./start-mcp.sh (Linux/macOS)")
        print("   start-mcp.bat (Windows)")
        sys.exit(1)
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Run quick tests")
    print("2. Interactive mode")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        run_quick_tests(client)
    elif choice == "2":
        interactive_mode(client)
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
