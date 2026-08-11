from fastapi import FastAPI
import uvicorn
import httpx

app = FastAPI()

XRAY_BASE_URL = "http://localhost:8000"  # adjust if different


@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/debug/issue/{issue_key}")
def debug_issue(issue_key: str):
    with httpx.Client(verify=False) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{issue_key}")

        return {
            "status_code": resp.status_code,
            "content_type": resp.headers.get("content-type"),
            "text": resp.text[:2000],  # IMPORTANT: safe preview
        }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)


# -- Tool 2: Confluence page ---------------------------------------------------

@app.get(
    "/confluence/page/{page_id}",
    operation_id="get_confluence_page",
    summary="Step 2: Retrieve and parse Test Plan SOP page from Confluence",
)
def get_confluence_page(page_id: str = CONFLUENCE_PAGE_ID):
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{LOCAL_API_URL}/page/{page_id}")

        if resp.status_code in (301, 302):
            redirect_url = resp.headers.get("location")
            resp = client.get(redirect_url)

        resp.raise_for_status()
        data = resp.json()

    html = data.get("body", "")
    if not html:
        raise HTTPException(status_code=404, detail="No HTML body found.")

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if table is None:
        raise HTTPException(status_code=404, detail="No table found.")

    rows = table.find_all("tr")
    if not rows:
        return []

    # Header row
    headers = [
        cell.get_text(" ", strip=True)
        for cell in rows[0].find_all(["th", "td"])
    ]

    result = []

    # Data rows
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        values = [
            cell.get_text(" ", strip=True)
            for cell in cells
        ]

        # Handle rows with missing columns due to rowspan/colspan
        while len(values) < len(headers):
            values.append(None)

        result.append(dict(zip(headers, values)))

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "space": data.get("space"),
        "version": data.get("version"),
        "rows": result
    }
