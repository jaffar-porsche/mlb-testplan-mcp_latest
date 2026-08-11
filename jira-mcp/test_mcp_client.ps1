#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test script for Jira MCP Server endpoints
.DESCRIPTION
    This script tests both the MCP protocol endpoint and the REST API endpoints
#>

param(
    [string]$Port = "8000",
    [string]$BaseUrl = "http://localhost:$Port"
)

Write-Host "Testing Jira MCP Server at $BaseUrl" -ForegroundColor Cyan
Write-Host "=" * 60

# Helper function for URL encoding
function Encode-Url($text) {
    return [System.Uri]::EscapeDataString($text)
}

# Test 1: Search Issues via REST API
Write-Host "`n[Test 1] Testing REST API - Search Issues (Recent)" -ForegroundColor Yellow
try {
    $jql = "order by created DESC"
    $encodedJql = Encode-Url $jql
    $response = Invoke-RestMethod -Uri "$BaseUrl/search_issues?jql=$encodedJql&max_results=5" -Method GET -ErrorAction Stop
    
    Write-Host "SUCCESS: Found $($response.total) issues (showing $($response.issue_count))" -ForegroundColor Green
    if ($response.issues) {
        $response.issues | Select-Object -First 3 | ForEach-Object {
            Write-Host "  - $($_.key): $($_.summary)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Get specific issue via REST API
Write-Host "`n[Test 2] Testing REST API - Get Issue Details" -ForegroundColor Yellow
try {
    # First get an issue key from search
    $jql = "order by created DESC"
    $encodedJql = Encode-Url $jql
    $searchResponse = Invoke-RestMethod -Uri "$BaseUrl/search_issues?jql=$encodedJql&max_results=1" -Method GET -ErrorAction Stop
    
    if ($searchResponse.issues -and $searchResponse.issues.Count -gt 0) {
        $issueKey = $searchResponse.issues[0].key
        $issueResponse = Invoke-RestMethod -Uri "$BaseUrl/issue/$issueKey" -Method GET -ErrorAction Stop
        
        Write-Host "SUCCESS: Retrieved issue $issueKey" -ForegroundColor Green
        Write-Host "  Summary: $($issueResponse.fields.summary)" -ForegroundColor Gray
        Write-Host "  Status: $($issueResponse.fields.status.name)" -ForegroundColor Gray
        Write-Host "  Type: $($issueResponse.fields.issuetype.name)" -ForegroundColor Gray
    } else {
        Write-Host "SKIPPED: No issues found to retrieve" -ForegroundColor Yellow
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Search issues by project via REST API
Write-Host "`n[Test 3] Testing REST API - Search Issues by Project" -ForegroundColor Yellow
try {
    $jql = "project = SLIM AND statusCategory != Done"
    $encodedJql = Encode-Url $jql
    $response = Invoke-RestMethod -Uri "$BaseUrl/search_issues?jql=$encodedJql&max_results=5" -Method GET -ErrorAction Stop
    
    Write-Host "SUCCESS: Found $($response.total) open SLIM issues (showing $($response.issue_count))" -ForegroundColor Green
    if ($response.issues) {
        $response.issues | ForEach-Object {
            Write-Host "  - $($_.key): [$($_.status)] $($_.summary)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Complex JQL search via REST API
Write-Host "`n[Test 4] Testing REST API - Complex JQL Query" -ForegroundColor Yellow
try {
    # Search for issues with specific criteria
    $jql = "statusCategory = 'In Progress' OR status = 'In Dev' ORDER BY updated DESC"
    $encodedJql = Encode-Url $jql
    $response = Invoke-RestMethod -Uri "$BaseUrl/search_issues?jql=$encodedJql&max_results=5" -Method GET -ErrorAction Stop
    
    Write-Host "SUCCESS: Found $($response.total) in-progress issues (showing $($response.issue_count))" -ForegroundColor Green
    if ($response.issues) {
        $response.issues | ForEach-Object {
            Write-Host "  - $($_.key): [$($_.status)] $($_.summary)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Get issue attachments via REST API
Write-Host "`n[Test 5] Testing REST API - Get Issue Attachments" -ForegroundColor Yellow
try {
    # First get an issue key from search
    $jql = "order by created DESC"
    $encodedJql = Encode-Url $jql
    $searchResponse = Invoke-RestMethod -Uri "$BaseUrl/search_issues?jql=$encodedJql&max_results=1" -Method GET -ErrorAction Stop
    
    if ($searchResponse.issues -and $searchResponse.issues.Count -gt 0) {
        $issueKey = $searchResponse.issues[0].key
        $attachmentsResponse = Invoke-RestMethod -Uri "$BaseUrl/issue/$issueKey/attachments" -Method GET -ErrorAction Stop
        
        Write-Host "SUCCESS: Retrieved attachments for $issueKey" -ForegroundColor Green
        if ($attachmentsResponse.attachments -and $attachmentsResponse.attachments.Count -gt 0) {
            Write-Host "  Found $($attachmentsResponse.attachments.Count) attachment(s):" -ForegroundColor Gray
            $attachmentsResponse.attachments | ForEach-Object {
                Write-Host "    - $($_.filename) ($($_.size) bytes)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  No attachments found" -ForegroundColor Gray
        }
    } else {
        Write-Host "SKIPPED: No issues found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 60)
Write-Host "Test completed!" -ForegroundColor Cyan
Write-Host "`nAPI Documentation: $BaseUrl/docs" -ForegroundColor Gray
Write-Host "OpenAPI Schema: $BaseUrl/openapi.json" -ForegroundColor Gray
