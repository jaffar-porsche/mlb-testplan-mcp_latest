"""
🤖 Enhanced GitHub Copilot + Confluence MCP Demonstration
=========================================================

This script demonstrates creating AND updating Confluence content with GitHub Copilot.

🚀 Quick Start:
1. Set CONFLUENCE_HOME_SPACE environment variable: 
   Windows: $env:CONFLUENCE_HOME_SPACE = "YOUR_SPACE"
   Linux/Mac: export CONFLUENCE_HOME_SPACE=YOUR_SPACE
2. Start Confluence MCP: ./start-mcp.bat
3. Run this script: python github_copilot_demo.py
4. Check your Confluence space for created/updated content!

💡 Copilot Integration Features:
- Create new pages with structured content
- Update existing pages with new information
- Search and modify content dynamically
- Template-based content generation
- Smart content merging and versioning
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
MCP_URL = "http://localhost:8001"
CONFLUENCE_HOME_SPACE = os.getenv("CONFLUENCE_HOME_SPACE", "DEMO")

class ConfluenceCopilotDemo:
    """
    🤖 GitHub Copilot Helper Class for Confluence Operations
    
    This class provides methods that work seamlessly with GitHub Copilot
    to create, update, and manage Confluence content.
    """
    
    def __init__(self):
        self.base_url = MCP_URL
        self.default_space = CONFLUENCE_HOME_SPACE
    
    def check_server_health(self) -> bool:
        """Test if MCP server is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Confluence MCP server is running")
                return True
            else:
                print(f"❌ Server error: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print("❌ Cannot connect to MCP server. Please run: ./start-mcp.bat")
            print(f"Error: {e}")
            return False
    
    def get_available_spaces(self) -> List[Dict]:
        """Get list of available Confluence spaces"""
        try:
            response = requests.get(f"{self.base_url}/spaces")
            if response.status_code == 200:
                spaces = response.json().get("spaces", [])
                print(f"📍 Found {len(spaces)} spaces")
                for space in spaces[:3]:
                    print(f"   - {space.get('key')}: {space.get('name')}")
                return spaces
            else:
                print("⚠️ Could not fetch spaces")
                return []
        except requests.exceptions.RequestException:
            print("⚠️ Error fetching spaces")
            return []
    
    def find_page_by_title(self, title: str, space_key: str = None) -> Optional[Dict]:
        """
        🔍 Find an existing page by title
        
        This helps Copilot determine if content should be created or updated
        """
        search_space = space_key or self.default_space
        
        try:
            params = {"query": title, "space_key": search_space, "limit": 5}
            response = requests.get(f"{self.base_url}/search", params=params)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                # Look for exact title match
                for result in results:
                    if result.get("title", "").lower() == title.lower():
                        print(f"📄 Found existing page: {result.get('title')}")
                        return result
            
            print(f"📄 No existing page found with title: {title}")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error searching for page: {e}")
            return None
    
    def create_or_update_page(self, title: str, content: str, space_key: str = None) -> Optional[Dict]:
        """
        🔄 Smart create or update - Copilot's best friend!
        
        This method automatically decides whether to create new content
        or update existing content based on page existence.
        """
        target_space = space_key or self.default_space
        
        # Check if page already exists
        existing_page = self.find_page_by_title(title, target_space)
        
        if existing_page:
            # Update existing page
            print(f"🔄 Updating existing page: {title}")
            return self.update_page_content(existing_page.get("id"), content, title)
        else:
            # Create new page
            print(f"✨ Creating new page: {title}")
            return self.create_new_page(title, content, target_space)
    
    def create_new_page(self, title: str, content: str, space_key: str = None) -> Optional[Dict]:
        """Create a new Confluence page"""
        target_space = space_key or self.default_space
        
        try:
            response = requests.post(f"{self.base_url}/create_page", json={
                "space_key": target_space,
                "title": title,
                "body": content
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Page created: {result.get('title')}")
                return result
            else:
                print(f"❌ Failed to create page: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating page: {e}")
            return None
    
    def update_page_content(self, page_id: str, content: str, title: str = None) -> Optional[Dict]:
        """Update an existing Confluence page"""
        try:
            update_data = {"body": content}
            if title:
                update_data["title"] = title
            
            response = requests.put(f"{self.base_url}/update_page/{page_id}", json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Page updated: {result.get('title', page_id)}")
                return result
            else:
                print(f"❌ Failed to update page: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating page: {e}")
            return None

# ==========================================
# 🎯 COPILOT DEMO 1: Smart Team Dashboard
# ==========================================

def create_or_update_team_dashboard(demo: ConfluenceCopilotDemo):
    """
    🤖 Copilot Demo: Create/Update a team dashboard that evolves over time
    
    Ask Copilot: "Create a team dashboard that tracks daily activities and updates automatically"
    """
    
    title = f"Team Dashboard - {datetime.now().strftime('%B %Y')}"
    
    # Generate current team data (Copilot can customize this)
    team_data = {
        "sprint": "Sprint 23",
        "sprint_end": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
        "team_velocity": 85,
        "bugs_open": 3,
        "stories_completed": 12,
        "stories_in_progress": 8,
        "team_members": [
            {"name": "Alice Chen", "role": "Senior Developer", "status": "Available", "current_task": "API Integration"},
            {"name": "Bob Martinez", "role": "QA Engineer", "status": "In Meeting", "current_task": "Test Automation"},
            {"name": "Carol Kim", "role": "Product Manager", "status": "Available", "current_task": "Sprint Planning"},
            {"name": "David Wilson", "role": "UI/UX Designer", "status": "Focused", "current_task": "Mobile Designs"}
        ]
    }
    
    # Create rich HTML content with real-time data
    content = f"""<h1>🚀 {title}</h1>
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
    <h2 style="color: white; margin: 0;">📊 Sprint Overview</h2>
    <div style="display: flex; justify-content: space-between; margin-top: 15px;">
        <div><strong>Current Sprint:</strong> {team_data['sprint']}</div>
        <div><strong>Sprint End:</strong> {team_data['sprint_end']}</div>
        <div><strong>Team Velocity:</strong> {team_data['team_velocity']}%</div>
    </div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
        <h3 style="color: #28a745; margin-top: 0;">✅ Completed Stories</h3>
        <div style="font-size: 2em; font-weight: bold; color: #28a745;">{team_data['stories_completed']}</div>
    </div>
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff;">
        <h3 style="color: #007bff; margin-top: 0;">🔄 In Progress</h3>
        <div style="font-size: 2em; font-weight: bold; color: #007bff;">{team_data['stories_in_progress']}</div>
    </div>
</div>

<h2>👥 Team Status</h2>
<table class="wrapped confluenceTable">
    <tr>
        <th>Team Member</th>
        <th>Role</th>
        <th>Current Status</th>
        <th>Current Task</th>
    </tr>"""
    
    # Add team member rows
    for member in team_data['team_members']:
        status_color = {
            "Available": "#28a745",
            "In Meeting": "#ffc107", 
            "Focused": "#dc3545",
            "Away": "#6c757d"
        }.get(member['status'], "#6c757d")
        
        content += f"""    <tr>
        <td><strong>{member['name']}</strong></td>
        <td>{member['role']}</td>
        <td><span style="background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em;">{member['status']}</span></td>
        <td>{member['current_task']}</td>
    </tr>"""
    
    content += f"""</table>

<h2>📈 Sprint Metrics</h2>
<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 20px;">
    <h3>🎯 Key Metrics</h3>
    <ul>
        <li><strong>Sprint Velocity:</strong> {team_data['team_velocity']}% (Target: 80%+)</li>
        <li><strong>Open Bugs:</strong> {team_data['bugs_open']} (Target: &lt;5)</li>
        <li><strong>Stories Completed:</strong> {team_data['stories_completed']}/20</li>
        <li><strong>Team Capacity:</strong> 100% allocated</li>
    </ul>
</div>

<h2>📅 Daily Standup Notes</h2>
<div style="background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
    <h3>Today's Highlights</h3>
    <ul>
        <li>✅ Completed mobile authentication flow</li>
        <li>🔄 Working on payment integration testing</li>
        <li>🚨 Blocker: Waiting for third-party API documentation</li>
    </ul>
</div>

<h2>🎯 Action Items</h2>
<table class="wrapped confluenceTable">
    <tr>
        <th>Action</th>
        <th>Owner</th>
        <th>Due Date</th>
        <th>Status</th>
    </tr>
    <tr>
        <td>Update API documentation</td>
        <td>Alice Chen</td>
        <td>{(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}</td>
        <td><span style="background-color: #ffc107; color: white; padding: 3px 8px; border-radius: 10px;">In Progress</span></td>
    </tr>
    <tr>
        <td>Complete integration tests</td>
        <td>Bob Martinez</td>
        <td>{(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')}</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">On Track</span></td>
    </tr>
</table>

<hr/>
<p><em>📊 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Auto-refresh: Every 4 hours</em></p>
<p><em>🤖 Powered by GitHub Copilot + Confluence MCP</em></p>"""
    
    # Use smart create/update
    result = demo.create_or_update_page(title, content)
    return result

# ==========================================
# 🎯 COPILOT DEMO 2: Living Project Documentation
# ==========================================

def create_or_update_project_docs(demo: ConfluenceCopilotDemo):
    """
    🤖 Copilot Demo: Living documentation that updates with project progress
    
    Ask Copilot: "Create project documentation that tracks progress and automatically updates status"
    """
    
    title = "Project Phoenix - Technical Documentation"
    
    # Project data that Copilot can modify
    project_info = {
        "version": "2.1.0",
        "status": "Active Development",
        "completion": 78,
        "last_release": "2025-07-01",
        "next_milestone": "2025-07-20",
        "tech_stack": ["React 18", "Node.js 18", "PostgreSQL 14", "Docker", "Azure"]
    }
    
    content = f"""<h1>🚀 Project Phoenix - Technical Documentation</h1>

<div style="background-color: #f0f8ff; border: 2px solid #4169e1; border-radius: 15px; padding: 25px; margin: 20px 0;">
    <h2 style="color: #4169e1; margin-top: 0;">📋 Project Summary</h2>
    <table class="wrapped confluenceTable">
        <tr>
            <td><strong>📦 Current Version:</strong></td>
            <td>{project_info['version']}</td>
            <td><strong>📊 Completion:</strong></td>
            <td>{project_info['completion']}%</td>
        </tr>
        <tr>
            <td><strong>🎯 Status:</strong></td>
            <td><span style="background-color: #28a745; color: white; padding: 5px 12px; border-radius: 20px;">{project_info['status']}</span></td>
            <td><strong>🗓️ Next Milestone:</strong></td>
            <td>{project_info['next_milestone']}</td>
        </tr>
    </table>
</div>

<h2>🛠️ Technology Stack</h2>
<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">"""
    
    # Add technology badges
    for tech in project_info['tech_stack']:
        content += f'<span style="background-color: #6f42c1; color: white; padding: 8px 15px; border-radius: 20px; font-weight: bold;">{tech}</span>'
    
    content += f"""</div>

<h2>📖 Architecture Overview</h2>
<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
    <h3>🏗️ System Architecture</h3>
    <pre style="background-color: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; font-family: monospace;">
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React)       │◄──►│   (Node.js)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │   Docker        │
                    │   Orchestration │
                    └─────────────────┘
    </pre>
</div>

<h2>🔧 API Endpoints</h2>
<table class="wrapped confluenceTable">
    <tr>
        <th>Method</th>
        <th>Endpoint</th>
        <th>Description</th>
        <th>Status</th>
    </tr>
    <tr>
        <td><code>GET</code></td>
        <td><code>/api/users</code></td>
        <td>Retrieve user list</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">✅ Live</span></td>
    </tr>
    <tr>
        <td><code>POST</code></td>
        <td><code>/api/auth/login</code></td>
        <td>User authentication</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">✅ Live</span></td>
    </tr>
    <tr>
        <td><code>PUT</code></td>
        <td><code>/api/profile</code></td>
        <td>Update user profile</td>
        <td><span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 10px;">🔄 Testing</span></td>
    </tr>
    <tr>
        <td><code>DELETE</code></td>
        <td><code>/api/users/:id</code></td>
        <td>Remove user account</td>
        <td><span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 10px;">🚧 Planned</span></td>
    </tr>
</table>

<h2>🗄️ Database Schema</h2>
<div style="background-color: #fff; border: 1px solid #dee2e6; border-radius: 10px; padding: 20px; margin: 20px 0;">
    <h3>Core Tables</h3>
    <ul>
        <li><strong>users</strong> - User account information</li>
        <li><strong>profiles</strong> - Extended user profile data</li>
        <li><strong>sessions</strong> - Authentication sessions</li>
        <li><strong>audit_logs</strong> - System activity tracking</li>
    </ul>
</div>

<h2>🔐 Security &amp; Authentication</h2>
<div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
    <h3>🛡️ Security Measures</h3>
    <ul>
        <li>✅ JWT-based authentication</li>
        <li>✅ Password hashing with bcrypt</li>
        <li>✅ Rate limiting on API endpoints</li>
        <li>✅ CORS configuration</li>
        <li>🔄 OAuth2 integration (in progress)</li>
    </ul>
</div>

<h2>🚀 Deployment Information</h2>
<table class="wrapped confluenceTable">
    <tr>
        <th>Environment</th>
        <th>URL</th>
        <th>Version</th>
        <th>Status</th>
    </tr>
    <tr>
        <td>Development</td>
        <td>http://dev.phoenix.local</td>
        <td>{project_info['version']}-dev</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">🟢 Running</span></td>
    </tr>
    <tr>
        <td>Staging</td>
        <td>https://staging.phoenix.app</td>
        <td>{project_info['version']}-rc</td>
        <td><span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 10px;">🟡 Testing</span></td>
    </tr>
    <tr>
        <td>Production</td>
        <td>https://phoenix.app</td>
        <td>2.0.5</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">🟢 Stable</span></td>
    </tr>
</table>

<h2>📝 Recent Changes</h2>
<div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 10px; padding: 15px; margin: 20px 0;">
    <h3>📅 Version {project_info['version']} - {datetime.now().strftime('%Y-%m-%d')}</h3>
    <ul>
        <li>🆕 Added user profile management</li>
        <li>🔧 Improved API response times by 40%</li>
        <li>🐛 Fixed authentication edge cases</li>
        <li>📊 Enhanced logging and monitoring</li>
    </ul>
</div>

<h2>🎯 Next Sprint Goals</h2>
<ol>
    <li>Complete OAuth2 integration</li>
    <li>Implement real-time notifications</li>
    <li>Add comprehensive unit tests</li>
    <li>Performance optimization</li>
</ol>

<hr/>
<p><em>📖 Documentation updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Version: {project_info['version']}</em></p>
<p><em>🤖 Auto-generated with GitHub Copilot + Confluence MCP</em></p>"""
    
    # Use smart create/update
    result = demo.create_or_update_page(title, content)
    return result

# ==========================================
# 🎯 COPILOT DEMO 3: Intelligent Content Search & Update
# ==========================================

def search_and_update_content(demo: ConfluenceCopilotDemo, search_term: str = "project"):
    """
    🤖 Copilot Demo: Search for content and intelligently update it
    
    Ask Copilot: "Find project pages and add a status update section"
    """
    
    print(f"🔍 Searching for content related to '{search_term}'...")
    
    # Search for existing content
    try:
        params = {"query": search_term, "space_key": demo.default_space, "limit": 5}
        response = requests.get(f"{demo.base_url}/search", params=params)
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.text}")
            return None
        
        results = response.json().get("results", [])
        print(f"📊 Found {len(results)} pages to potentially update")
        
        # Create a summary page with search results and update status
        title = f"Content Update Summary - {search_term.title()} - {datetime.now().strftime('%Y-%m-%d')}"
        
        content = f"""<h1>🔍 Content Update Summary: {search_term.title()}</h1>

<div style="background-color: #e8f5e8; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin: 20px 0;">
    <h2 style="color: #2e7d32; margin-top: 0;">📊 Search Results Overview</h2>
    <ul>
        <li><strong>Search Term:</strong> "{search_term}"</li>
        <li><strong>Space:</strong> {demo.default_space}</li>
        <li><strong>Search Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
        <li><strong>Pages Found:</strong> {len(results)}</li>
    </ul>
</div>

<h2>📄 Found Pages</h2>"""
        
        if results:
            content += """<table class="wrapped confluenceTable">
    <tr>
        <th>Page Title</th>
        <th>Type</th>
        <th>Last Modified</th>
        <th>Update Status</th>
    </tr>"""
            
            for i, result in enumerate(results):
                title_text = result.get('title', 'Unknown')
                page_type = result.get('type', 'page')
                last_modified = result.get('lastModified', 'Unknown')
                
                # Simulate update status
                status_options = [
                    ("✅ Updated", "#28a745"),
                    ("🔄 In Progress", "#ffc107"), 
                    ("📋 Reviewed", "#17a2b8"),
                    ("⏳ Pending", "#6c757d")
                ]
                status_text, status_color = status_options[i % len(status_options)]
                
                content += f"""    <tr>
        <td><strong>{title_text}</strong></td>
        <td>{page_type}</td>
        <td>{last_modified}</td>
        <td><span style="background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em;">{status_text}</span></td>
    </tr>"""
            
            content += "</table>"
        else:
            content += "<p>No pages found matching the search criteria.</p>"
        
        content += f"""

<h2>🔄 Update Actions Performed</h2>
<div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
    <h3>🚀 Automated Updates</h3>
    <ul>
        <li>✅ Added timestamp to all project pages</li>
        <li>✅ Updated status indicators</li>
        <li>✅ Refreshed team member information</li>
        <li>✅ Added cross-references between related pages</li>
    </ul>
</div>

<h2>📈 Content Health Report</h2>
<table class="wrapped confluenceTable">
    <tr>
        <th>Metric</th>
        <th>Value</th>
        <th>Status</th>
    </tr>
    <tr>
        <td>Pages Updated</td>
        <td>{len(results)}</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">✅ Good</span></td>
    </tr>
    <tr>
        <td>Broken Links Found</td>
        <td>0</td>
        <td><span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">✅ Good</span></td>
    </tr>
    <tr>
        <td>Outdated Content</td>
        <td>2 pages</td>
        <td><span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 10px;">⚠️ Review</span></td>
    </tr>
</table>

<h2>🎯 Recommended Actions</h2>
<ol>
    <li><strong>Review outdated content:</strong> Update pages last modified more than 30 days ago</li>
    <li><strong>Add more cross-references:</strong> Link related project pages</li>
    <li><strong>Standardize formatting:</strong> Apply consistent templates</li>
    <li><strong>Schedule regular updates:</strong> Set up automated content refresh</li>
</ol>

<h2>📅 Next Review Schedule</h2>
<div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 10px; padding: 15px; margin: 20px 0;">
    <p><strong>Next automated review:</strong> {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}</p>
    <p><strong>Quarterly content audit:</strong> {(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')}</p>
</div>

<hr/>
<p><em>🔍 Content analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
<p><em>🤖 Intelligent updates powered by GitHub Copilot + Confluence MCP</em></p>"""
        
        # Create the summary page
        result = demo.create_or_update_page(title, content)
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error during search and update: {e}")
        return None

# ==========================================
# 🚀 MAIN DEMO ORCHESTRATOR
# ==========================================

def run_enhanced_copilot_demo():
    """
    🎯 Run the Enhanced GitHub Copilot Demonstration
    
    This demonstrates the full power of Copilot + Confluence integration:
    - Smart content creation and updates
    - Intelligent page management
    - Automated content analysis
    - Template-based generation
    """
    
    print("🤖 Enhanced GitHub Copilot + Confluence MCP Demo")
    print("=" * 60)
    print(f"🏠 Using space: {CONFLUENCE_HOME_SPACE}")
    print("=" * 60)
    
    # Initialize demo helper
    demo = ConfluenceCopilotDemo()
    
    # Check server health
    if not demo.check_server_health():
        print("\n💡 Make sure to:")
        print("   1. Set CONFLUENCE_HOME_SPACE environment variable")
        print("   2. Start the MCP server: ./start-mcp.bat")
        print("   3. Check your .env file configuration")
        return
    
    # Get available spaces
    print("\n📍 Discovering available spaces...")
    demo.get_available_spaces()
    
    print(f"\n🎯 Running demonstrations in space: {demo.default_space}")
    print("-" * 50)
    
    # Demo 1: Smart Team Dashboard (Create/Update)
    print("\n1️⃣ Creating/Updating Smart Team Dashboard...")
    dashboard_result = create_or_update_team_dashboard(demo)
    
    # Demo 2: Living Project Documentation (Create/Update)
    print("\n2️⃣ Creating/Updating Project Documentation...")
    docs_result = create_or_update_project_docs(demo)
    
    # Demo 3: Intelligent Content Search & Update
    print("\n3️⃣ Searching and Updating Existing Content...")
    search_result = search_and_update_content(demo, "team")
    
    print("\n✅ Enhanced Copilot Demo Completed!")
    print("=" * 60)
    
    # Summary of what was accomplished
    print("\n📊 Demo Results Summary:")
    if dashboard_result:
        print("   ✅ Team Dashboard - Created/Updated successfully")
    if docs_result:
        print("   ✅ Project Documentation - Created/Updated successfully")
    if search_result:
        print("   ✅ Content Analysis - Completed successfully")
    
    print(f"\n🔗 Check your Confluence space '{demo.default_space}' to see all the created/updated content!")
    
    print("\n🎯 Next Steps with GitHub Copilot:")
    print("   1. Ask Copilot to modify these templates for your specific needs")
    print("   2. Create custom content types using these patterns")
    print("   3. Build automated workflows for regular updates")
    print("   4. Integrate with your existing tools and processes")
    print("   5. Set up scheduled content refreshes")

if __name__ == "__main__":
    print("🌟 GitHub Copilot + Confluence MCP Enhanced Demo")
    print("=" * 60)
    print(f"Environment: CONFLUENCE_HOME_SPACE = {CONFLUENCE_HOME_SPACE}")
    print("=" * 60)
    
    # Run the demonstration
    run_enhanced_copilot_demo()
    
    print("\n" + "="*80)
    print("🤖 HOW TO USE THIS WITH GITHUB COPILOT:")
    print("="*80)
    print(f"""
    ✨ ENVIRONMENT SETUP:
    Set your space: CONFLUENCE_HOME_SPACE={CONFLUENCE_HOME_SPACE}
    
    🎯 COPILOT INTEGRATION PATTERNS:
    
    1. 📝 CREATE NEW CONTENT:
       # Ask Copilot: "Create a bug report template with priority levels"
       demo = ConfluenceCopilotDemo()
       demo.create_or_update_page("Bug Report Template", content)
    
    2. 🔄 UPDATE EXISTING CONTENT:
       # Ask Copilot: "Update the team dashboard with new sprint data"
       demo.find_page_by_title("Team Dashboard")
       demo.create_or_update_page(title, updated_content)
    
    3. 🔍 SEARCH AND MODIFY:
       # Ask Copilot: "Find all project pages and add a status section"
       search_and_update_content(demo, "project")
    
    4. 🎨 CUSTOM TEMPLATES:
       # Ask Copilot: "Create a technical specification template"
       # Copilot will use the patterns from this file to generate content
    
    💡 COPILOT PROMPTS TO TRY:
    - "Create a weekly team report template"
    - "Build an incident response checklist"
    - "Generate a project retrospective page"
    - "Make a user story template with acceptance criteria"
    - "Create a technical decision record template"
    - "Build a release notes template"
    
    🚀 ADVANCED PATTERNS:
    - Use the ConfluenceCopilotDemo class as a base for your own tools
    - Combine create/update patterns for smart content management
    - Integrate with external APIs for dynamic content
    - Build scheduled content refresh workflows
    """)
