#!/usr/bin/env python3
"""
Example script demonstrating how to upload attachments to JIRA issues
using the JIRA MCP Server.
"""

import requests
import base64
import os

# Configuration
MCP_SERVER_URL = "http://localhost:8000"
ISSUE_KEY = "ITDMFC-1496"  # Replace with your issue key

def upload_attachment(issue_key: str, file_path: str):
    """
    Upload a file attachment to a JIRA issue via the MCP server.
    
    Args:
        issue_key: The JIRA issue key (e.g., "ITDMFC-1496")
        file_path: Path to the file to upload
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    url = f"{MCP_SERVER_URL}/issue/{issue_key}/attachments"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result['message']}")
        print(f"   File: {result['attachment']['filename']}")
        print(f"   Size: {result['attachment']['size']} bytes")
        print(f"   ID: {result['attachment']['id']}")
        print(f"   URL: {result['issue_url']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")

def list_attachments(issue_key: str):
    """
    List all attachments on a JIRA issue.
    
    Args:
        issue_key: The JIRA issue key (e.g., "ITDMFC-1496")
    """
    url = f"{MCP_SERVER_URL}/issue/{issue_key}/attachments"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n📎 Attachments for {issue_key}:")
        print(f"   Total: {result['attachment_count']}")
        
        for att in result['attachments']:
            print(f"\n   - {att['filename']}")
            print(f"     ID: {att['id']}")
            print(f"     Size: {att['size']} bytes")
            print(f"     Type: {att['mimeType']}")
            print(f"     Created: {att['created']}")
            print(f"     Author: {att['author']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")

def delete_attachment(issue_key: str, attachment_id: str):
    """
    Delete an attachment from a JIRA issue.
    
    Args:
        issue_key: The JIRA issue key (e.g., "ITDMFC-1496")
        attachment_id: The ID of the attachment to delete
    """
    url = f"{MCP_SERVER_URL}/issue/{issue_key}/attachments/{attachment_id}"
    response = requests.delete(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Upload:  python upload_attachment.py upload <issue_key> <file_path>")
        print("  List:    python upload_attachment.py list <issue_key>")
        print("  Delete:  python upload_attachment.py delete <issue_key> <attachment_id>")
        print("\nExample:")
        print("  python upload_attachment.py upload ITDMFC-1496 document.pdf")
        print("  python upload_attachment.py list ITDMFC-1496")
        print("  python upload_attachment.py delete ITDMFC-1496 12345")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "upload":
        if len(sys.argv) != 4:
            print("Error: Usage: python upload_attachment.py upload <issue_key> <file_path>")
            sys.exit(1)
        issue_key = sys.argv[2]
        file_path = sys.argv[3]
        upload_attachment(issue_key, file_path)
        
    elif command == "list":
        if len(sys.argv) != 3:
            print("Error: Usage: python upload_attachment.py list <issue_key>")
            sys.exit(1)
        issue_key = sys.argv[2]
        list_attachments(issue_key)
        
    elif command == "delete":
        if len(sys.argv) != 4:
            print("Error: Usage: python upload_attachment.py delete <issue_key> <attachment_id>")
            sys.exit(1)
        issue_key = sys.argv[2]
        attachment_id = sys.argv[3]
        delete_attachment(issue_key, attachment_id)
        
    else:
        print(f"Error: Unknown command: {command}")
        print("Available commands: upload, list, delete")
        sys.exit(1)
