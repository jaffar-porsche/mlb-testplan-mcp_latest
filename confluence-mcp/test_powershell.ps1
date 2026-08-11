# Confluence MCP Server - PowerShell Test Commands
# 
# Make sure the server is running before executing these commands:
# start-mcp.bat

$BaseUrl = "http://localhost:8001"
$SpaceKey = "TEST"  # Change this to a valid space key

Write-Host "🧪 Confluence MCP Server - PowerShell Test Commands" -ForegroundColor Cyan
Write-Host "=" * 50

# Test 1: List Spaces
Write-Host "`n1. List Spaces:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/spaces" -Method GET
    $response | ConvertTo-Json -Depth 5
    Write-Host "✅ Found $($response.total) spaces" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Search Content
Write-Host "`n2. Search Content:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/search?query=test&limit=5" -Method GET
    $response | ConvertTo-Json -Depth 5
    Write-Host "✅ Found $($response.total) results" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Create Page
Write-Host "`n3. Create Page:" -ForegroundColor Yellow
$pageData = @{
    space_key = $SpaceKey
    title = "Test Page from PowerShell"
    body = "<h1>Test Page</h1><p>This is a test page created via PowerShell.</p><p><strong>Created:</strong> $(Get-Date)</p>"
} | ConvertTo-Json

try {
    $createResponse = Invoke-RestMethod -Uri "$BaseUrl/create_page" -Method POST -Body $pageData -ContentType "application/json"
    $createResponse | ConvertTo-Json -Depth 5
    $pageId = $createResponse.id
    Write-Host "✅ Created page with ID: $pageId" -ForegroundColor Green
    
    # Test 4: Get Page
    if ($pageId) {
        Write-Host "`n4. Get Page Details:" -ForegroundColor Yellow
        try {
            $pageResponse = Invoke-RestMethod -Uri "$BaseUrl/page/$pageId" -Method GET
            $pageResponse | ConvertTo-Json -Depth 5
            Write-Host "✅ Retrieved page: $($pageResponse.title)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to get page: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Test 5: Update Page
        Write-Host "`n5. Update Page:" -ForegroundColor Yellow
        $updateData = @{
            title = "Updated Test Page from PowerShell"
            body = "<h1>Updated Test Page</h1><p>This page has been updated via PowerShell.</p><p><strong>Updated:</strong> $(Get-Date)</p>"
        } | ConvertTo-Json
        
        try {
            $updateResponse = Invoke-RestMethod -Uri "$BaseUrl/page/$pageId" -Method PUT -Body $updateData -ContentType "application/json"
            $updateResponse | ConvertTo-Json -Depth 5
            Write-Host "✅ Updated page to version $($updateResponse.version)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to update page: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "❌ Failed to create page: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Make sure space '$SpaceKey' exists or change the SpaceKey variable" -ForegroundColor Blue
}

# Test 6: Search in Specific Space
Write-Host "`n6. Search in Specific Space:" -ForegroundColor Yellow
try {
    $searchResponse = Invoke-RestMethod -Uri "$BaseUrl/search?query=test&space_key=$SpaceKey&limit=3" -Method GET
    $searchResponse | ConvertTo-Json -Depth 5
    Write-Host "✅ Found $($searchResponse.total) results in space $SpaceKey" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ PowerShell tests completed!" -ForegroundColor Green
