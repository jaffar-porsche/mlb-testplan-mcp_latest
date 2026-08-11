#!/bin/bash
# Test script for Jira MCP Server

PORT="${1:-8000}"
BASE_URL="http://localhost:$PORT"

echo "Testing Jira MCP Server at $BASE_URL"
echo "============================================================"

# Test 1: REST API - Search Issues (Recent)
echo -e "\n[Test 1] Testing REST API - Search Issues (Recent)"
RESPONSE=$(curl -s "$BASE_URL/search_issues?jql=order%20by%20created%20DESC&max_results=5")
if [ $? -eq 0 ]; then
    if command -v jq &> /dev/null; then
        echo "$RESPONSE" | jq -r '"SUCCESS: Found \(.total) issues (showing \(.issue_count))"'
        echo "$RESPONSE" | jq -r '.issues[:3][] | "  - \(.key): \(.summary)"'
    else
        echo "SUCCESS: Response received (install jq for formatted output)"
        echo "$RESPONSE" | grep -o '"key":"[^"]*"' | head -3
    fi
else
    echo "FAILED"
fi

# Test 2: REST API - Get Issue Details
echo -e "\n[Test 2] Testing REST API - Get Issue Details"
SEARCH_RESP=$(curl -s "$BASE_URL/search_issues?jql=order%20by%20created%20DESC&max_results=1")
if command -v jq &> /dev/null; then
    ISSUE_KEY=$(echo "$SEARCH_RESP" | jq -r '.issues[0].key' 2>/dev/null)
else
    ISSUE_KEY=$(echo "$SEARCH_RESP" | grep -o '"key":"[^"]*"' | head -1 | cut -d'"' -f4)
fi

if [ -n "$ISSUE_KEY" ] && [ "$ISSUE_KEY" != "null" ]; then
    ISSUE_RESPONSE=$(curl -s "$BASE_URL/issue/$ISSUE_KEY")
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Retrieved issue $ISSUE_KEY"
        if command -v jq &> /dev/null; then
            echo "$ISSUE_RESPONSE" | jq -r '"  Summary: \(.fields.summary)"'
            echo "$ISSUE_RESPONSE" | jq -r '"  Status: \(.fields.status.name)"'
            echo "$ISSUE_RESPONSE" | jq -r '"  Type: \(.fields.issuetype.name)"'
        else
            echo "  (install jq for formatted details)"
        fi
    else
        echo "FAILED"
    fi
else
    echo "SKIPPED: No issues found to retrieve"
fi

# Test 3: REST API - Search Issues by Project
echo -e "\n[Test 3] Testing REST API - Search Issues by Project"
JQL="project%20%3D%20SLIM%20AND%20statusCategory%20!%3D%20Done"
RESPONSE=$(curl -s "$BASE_URL/search_issues?jql=$JQL&max_results=5")
if [ $? -eq 0 ]; then
    if command -v jq &> /dev/null; then
        echo "$RESPONSE" | jq -r '"SUCCESS: Found \(.total) open SLIM issues (showing \(.issue_count))"'
        echo "$RESPONSE" | jq -r '.issues[] | "  - \(.key): [\(.status)] \(.summary)"'
    else
        echo "SUCCESS: Response received (install jq for formatted output)"
        echo "$RESPONSE" | grep -o '"key":"[^"]*"' | head -5
    fi
else
    echo "FAILED"
fi

# Test 4: REST API - Complex JQL Query
echo -e "\n[Test 4] Testing REST API - Complex JQL Query"
JQL="statusCategory%20%3D%20'In%20Progress'%20OR%20status%20%3D%20'In%20Dev'%20ORDER%20BY%20updated%20DESC"
RESPONSE=$(curl -s "$BASE_URL/search_issues?jql=$JQL&max_results=5")
if [ $? -eq 0 ]; then
    if command -v jq &> /dev/null; then
        echo "$RESPONSE" | jq -r '"SUCCESS: Found \(.total) in-progress issues (showing \(.issue_count))"'
        echo "$RESPONSE" | jq -r '.issues[] | "  - \(.key): [\(.status)] \(.summary)"'
    else
        echo "SUCCESS: Response received (install jq for formatted output)"
        echo "$RESPONSE" | grep -o '"key":"[^"]*"' | head -5
    fi
else
    echo "FAILED"
fi

# Test 5: REST API - Get Issue Attachments
echo -e "\n[Test 5] Testing REST API - Get Issue Attachments"
SEARCH_RESP2=$(curl -s "$BASE_URL/search_issues?jql=order%20by%20created%20DESC&max_results=1")
if command -v jq &> /dev/null; then
    ISSUE_KEY=$(echo "$SEARCH_RESP2" | jq -r '.issues[0].key' 2>/dev/null)
else
    ISSUE_KEY=$(echo "$SEARCH_RESP2" | grep -o '"key":"[^"]*"' | head -1 | cut -d'"' -f4)
fi

if [ -n "$ISSUE_KEY" ] && [ "$ISSUE_KEY" != "null" ]; then
    ATTACH_RESPONSE=$(curl -s "$BASE_URL/issue/$ISSUE_KEY/attachments")
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Retrieved attachments for $ISSUE_KEY"
        if command -v jq &> /dev/null; then
            ATTACH_COUNT=$(echo "$ATTACH_RESPONSE" | jq -r '.attachments | length')
            if [ "$ATTACH_COUNT" -gt 0 ]; then
                echo "  Found $ATTACH_COUNT attachment(s):"
                echo "$ATTACH_RESPONSE" | jq -r '.attachments[] | "    - \(.filename) (\(.size) bytes)"'
            else
                echo "  No attachments found"
            fi
        else
            ATTACH_COUNT=$(echo "$ATTACH_RESPONSE" | grep -o '"filename"' | wc -l)
            echo "  Found $ATTACH_COUNT attachment(s) (install jq for details)"
        fi
    else
        echo "FAILED"
    fi
else
    echo "SKIPPED: No issues found"
fi

echo -e "\n============================================================"
echo "Test completed!"
echo ""
echo "API Documentation: $BASE_URL/docs"
echo "OpenAPI Schema: $BASE_URL/openapi.json"
