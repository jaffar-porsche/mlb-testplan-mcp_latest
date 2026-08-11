import re
import os
import httpx
from fastapi import FastAPI, Query, Body
from fastapi_mcp import FastApiMCP
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
import json
from bs4 import BeautifulSoup
from fastapi import HTTPException
import time
from functools import wraps
import io
import pandas as pd
from fastapi.responses import StreamingResponse
import html as _html

"""xRay FAIL Report — single endpoint that retrieves all FAIL test results with KPM IDs.

Handles both issue types automatically:
- Test Plan  → JQL testrunstatus query, paginate testruns, extract run details
- Test (single) → find all linked test executions, get run details for each
"""
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from fastapi import HTTPException



logger = logging.getLogger(__name__)

# Max pages to scan when paginating test runs (100 runs/page = 2000 max)
_MAX_PAGES = 20
# Max parallel threads for fetching run details
_MAX_WORKERS = 20

# KPM patterns to search in run comments / actual results
_KPM_PATTERNS = [
    re.compile(r"[Kk][Pp][Mm]\s*[:\-–]\s*(?:\[.*?\])?\s*(\d{7,})", re.IGNORECASE),
    re.compile(r"[Kk][Pp][Mm]\s*[Pp]roblem\s*[-–]?\s*(\d{7,})", re.IGNORECASE),
    re.compile(r"kpmweb[^\s]*[?&]id=(\d{7,})", re.IGNORECASE),
    re.compile(r"\bKPM\b\s+(\d{7,})"),

]

load_dotenv()

XRAY_BASE_URL = os.getenv("XRAY_BASE_URL", "http://localhost:8000")
LOCAL_API_URL  = os.getenv("LOCAL_API_URL",  "http://localhost:8001")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "2378907792")
PROXY = os.getenv("HTTP_PROXY", "http://http-proxy.porsche.org:3133")

ALIASES = {
    # ==========================================================
    # TEST RESULTS / STATUS
    # ==========================================================
    "pass": "PASS",
    "passed": "PASS",
    "passing": "PASS",
    "successful": "PASS",
    "success": "PASS",
    "ok": "PASS",
    "green": "PASS",
    "all good": "PASS",
    "working": "PASS",
    "works": "PASS",
    "completed": "PASS",
    "done": "PASS",
    "verified": "PASS",
    "valid": "PASS",
    "clear": "PASS",
    "clean": "PASS",

    "fail": "FAIL",
    "failed": "FAIL",
    "failure": "FAIL",
    "failures": "FAIL",
    "failing": "FAIL",
    "error": "FAIL",
    "errors": "FAIL",
    "red": "FAIL",
    "broken": "FAIL",
    "broke": "FAIL",
    "issue": "FAIL",
    "issues": "FAIL",
    "defect": "FAIL",
    "defects": "FAIL",
    "bug": "FAIL",
    "bugs": "FAIL",
    "regression": "FAIL",
    "regressions": "FAIL",
    "failing tests": "FAIL",
    "failed tests": "FAIL",
    "not working": "FAIL",
    "not pass": "FAIL",
    "not passed": "FAIL",
    "unsuccessful": "FAIL",
    "ko": "FAIL",

    "blocked": "BLOCKED",
    "block": "BLOCKED",
    "blocking": "BLOCKED",
    "blocker": "BLOCKED",
    "blockers": "BLOCKED",
    "on hold": "BLOCKED",
    "stuck": "BLOCKED",
    "impediment": "BLOCKED",
    "impediments": "BLOCKED",
    "cannot proceed": "BLOCKED",
    "waiting": "BLOCKED",
    "held": "BLOCKED",
    "hold": "BLOCKED",

    "aborted": "ABORTED",
    "abort": "ABORTED",
    "aborting": "ABORTED",
    "cancelled": "ABORTED",
    "canceled": "ABORTED",
    "terminated": "ABORTED",
    "stopped": "ABORTED",
    "skipped": "ABORTED",
    "skip": "ABORTED",
    "dropped": "ABORTED",
    "abandoned": "ABORTED",
    "removed": "ABORTED",
    "killed": "ABORTED",
    "interrupted": "ABORTED",

    "todo": "ToDo",
    "to do": "ToDo",
    "to-do": "ToDo",
    "pending": "ToDo",
    "not started": "ToDo",
    "notstarted": "ToDo",
    "not run": "ToDo",
    "not executed": "ToDo",
    "not tested": "ToDo",
    "untested": "ToDo",
    "queued": "ToDo",
    "backlog": "ToDo",
    "open": "ToDo",
    "new": "ToDo",
    "planned": "ToDo",
    "scheduled": "ToDo",

    "executing": "Executing",
    "execute": "Executing",
    "execution": "Executing",
    "running": "Executing",
    "run": "Executing",
    "in progress": "Executing",
    "processing": "Executing",
    "active": "Executing",
    "ongoing": "Executing",
    "in execution": "Executing",
    "under test": "Executing",
    "being tested": "Executing",
    "currently running": "Executing",
    "wip": "Executing",
    "work in progress": "Executing",

    # ==========================================================
    # REGIONS / MARKETS
    # ==========================================================
    # Europe
    "ece": "Testing ECE",
    "eu": "Testing ECE",
    "europe": "Testing ECE",
    "european": "Testing ECE",
    "emea": "Testing ECE",
    "eur": "Testing ECE",
    "euros": "Testing ECE",
    "central europe": "Testing ECE",
    "eastern europe": "Testing ECE",
    "western europe": "Testing ECE",
    "germany": "Testing ECE",
    "de": "Testing ECE",
    "france": "Testing ECE",
    "uk": "Testing ECE",
    "united kingdom": "Testing ECE",
    "spain": "Testing ECE",
    "italy": "Testing ECE",
    "netherlands": "Testing ECE",

    # North America
    "nar": "Testing NAR",
    "na": "Testing NAR",
    "north america": "Testing NAR",
    "north american": "Testing NAR",
    "america": "Testing NAR",
    "usa": "Testing NAR",
    "us": "Testing NAR",
    "united states": "Testing NAR",
    "canada": "Testing NAR",
    "u.s.": "Testing NAR",
    "u.s.a.": "Testing NAR",
    "american": "Testing NAR",
    "americas": "Testing NAR",
    "mexico": "Testing NAR",
    "mx": "Testing NAR",

    # Japan
    "jpn": "Testing JPN",
    "jp": "Testing JPN",
    "jap": "Testing JPN",
    "japan": "Testing JPN",
    "japanese": "Testing JPN",
    "nippon": "Testing JPN",
    "nihon": "Testing JPN",
    "tokyo": "Testing JPN",
    "osaka": "Testing JPN",
    "j market": "Testing JPN",

    # Korea
    "kor": "Testing KOR",
    "kr": "Testing KOR",
    "korea": "Testing KOR",
    "south korea": "Testing KOR",
    "korean": "Testing KOR",
    "republic of korea": "Testing KOR",
    "rok": "Testing KOR",
    "seoul": "Testing KOR",
    "k market": "Testing KOR",
    "sk": "Testing KOR",

    # Taiwan
    "twn": "Testing TWN",
    "tw": "Testing TWN",
    "taiwan": "Testing TWN",
    "taipei": "Testing TWN",
    "taiwanese": "Testing TWN",
    "twan": "Testing TWN",      # typo found in HTML
    "republic of china": "Testing TWN",
    "roc": "Testing TWN",
    "formosa": "Testing TWN",

    # Hong Kong
    "hk": "Testing Hong-Kong",
    "hkg": "Testing Hong-Kong",
    "hong kong": "Testing Hong-Kong",
    "hong-kong": "Testing Hong-Kong",
    "hongkong": "Testing Hong-Kong",
    "hksar": "Testing Hong-Kong",
    "hong kong sar": "Testing Hong-Kong",

    # Macau
    "macau": "Testing Macau",
    "macao": "Testing Macau",
    "mo": "Testing Macau",
    "mac": "Testing Macau",
    "macau sar": "Testing Macau",

    # ==========================================================
    # WORKSTREAMS
    # ==========================================================
    "applications": "WS Applications",
    "application": "WS Applications",
    "app": "WS Applications",
    "apps": "WS Applications",
    "ws applications": "WS Applications",
    "ws apps": "WS Applications",
    "workstream applications": "WS Applications",
    "ws app": "WS Applications",
    "application workstream": "WS Applications",

    "platform": "WS Platform",
    "ws platform": "WS Platform",
    "platform ws": "WS Platform",
    "workstream platform": "WS Platform",
    "plat": "WS Platform",
    "plt": "WS Platform",

    "system": "WS System",
    "systems": "WS System",
    "ws system": "WS System",
    "system ws": "WS System",
    "workstream system": "WS System",
    "sys": "WS System",
    "syst": "WS System",

    # ==========================================================
    # WORKING GROUPS
    # ==========================================================
    # Navigation
    "navigation": "Navigation",
    "nav": "Navigation",
    "maps": "Navigation",
    "map": "Navigation",
    "navi": "Navigation",
    "gps": "Navigation",
    "routing": "Navigation",
    "route": "Navigation",
    "directions": "Navigation",
    "location services": "Navigation",
    "poi": "Navigation",
    "points of interest": "Navigation",
    "here maps": "Navigation",
    "google maps": "Navigation",

    # Phone Connectivity SPI
    "phone": "Phone-Connectivity-SPI",
    "phone connectivity": "Phone-Connectivity-SPI",
    "phone-connectivity": "Phone-Connectivity-SPI",
    "phone connectivity spi": "Phone-Connectivity-SPI",
    "phone-connectivity-spi": "Phone-Connectivity-SPI",
    "[phone-connectivity]-spi": "Phone-Connectivity-SPI",
    "connectivity": "Phone-Connectivity-SPI",
    "mobile connectivity": "Phone-Connectivity-SPI",
    "spi": "Phone-Connectivity-SPI",
    "smartphone integration": "Phone-Connectivity-SPI",
    "mobile": "Phone-Connectivity-SPI",
    "bluetooth": "Phone-Connectivity-SPI",
    "bt": "Phone-Connectivity-SPI",
    "carplay": "Phone-Connectivity-SPI",
    "apple carplay": "Phone-Connectivity-SPI",
    "android auto": "Phone-Connectivity-SPI",
    "wireless": "Phone-Connectivity-SPI",
    "wifi": "Phone-Connectivity-SPI",
    "wi-fi": "Phone-Connectivity-SPI",
    "usb": "Phone-Connectivity-SPI",
    "mirroring": "Phone-Connectivity-SPI",
    "projection": "Phone-Connectivity-SPI",
    "tethering": "Phone-Connectivity-SPI",
    "hotspot": "Phone-Connectivity-SPI",
    #jaf added new working groups 07.07.2026
    
    # System Audio
    "system audio": "System Audio",
    "audio": "System Audio",
    "sound": "System Audio",
    "speaker": "System Audio",
    "speakers": "System Audio",
    "volume": "System Audio",
    "mute": "System Audio",
    "microphone": "System Audio",
    "mic": "System Audio",
    "voice audio": "System Audio",
    "audio system": "System Audio",
    "sound system": "System Audio",
    "amplifier": "System Audio",
    "amp": "System Audio",
    "equalizer": "System Audio",
    "eq": "System Audio",


    # Car
    "car": "Car",
    "vehicle": "Car",
    "automobile": "Car",
    "auto": "Car",
    "car settings": "Car",
    "vehicle settings": "Car",
    "driving": "Car",
    "drive": "Car",
    "door": "Car",
    "doors": "Car",
    "lock": "Car",
    "locks": "Car",
    "window": "Car",
    "windows": "Car",
    "lighting": "Car",
    "lights": "Car",
    "headlight": "Car",
    "climate": "Car",
    "climate control": "Car",
    "hvac": "Car",
    "seat": "Car",
    "seats": "Car",
    "steering": "Car",
    "mirror": "Car",
    "mirrors": "Car",

    # Sport Apps
    "sport apps": "Sport Apps",
    "sport app": "Sport Apps",
    "sports apps": "Sport Apps",
    "sports app": "Sport Apps",
    "sport": "Sport Apps",
    "sports": "Sport Apps",
    "fitness": "Sport Apps",
    "exercise": "Sport Apps",
    "workout": "Sport Apps",
    "training": "Sport Apps",
    "activity": "Sport Apps",
    "activities": "Sport Apps",
    "running": "Sport Apps",
    "cycling": "Sport Apps",
    "health": "Sport Apps",
    "wellness": "Sport Apps",

    # Core HMI / GBK
    "hmi": "Core HMI / GBK",
    "core hmi": "Core HMI / GBK",
    "core": "Core HMI / GBK",
    "gbk": "Core HMI / GBK",
    "gui": "Core HMI / GBK",
    "human machine interface": "Core HMI / GBK",
    "user interface": "Core HMI / GBK",
    "ui": "Core HMI / GBK",
    "ux": "Core HMI / GBK",
    "cockpit": "Core HMI / GBK",
    "display": "Core HMI / GBK",
    "screen": "Core HMI / GBK",
    "dashboard": "Core HMI / GBK",
    "instrument cluster": "Core HMI / GBK",
    "cluster": "Core HMI / GBK",
    "touchscreen": "Core HMI / GBK",
    "touch": "Core HMI / GBK",
    "gesture": "Core HMI / GBK",
    "infotainment display": "Core HMI / GBK",
    "head unit": "Core HMI / GBK",
    "hu": "Core HMI / GBK",
    "central display": "Core HMI / GBK",
    "pivi": "Core HMI / GBK",
    "pcm": "Core HMI / GBK",

    # Media / Tuner
    "media": "Media / Tuner (Entertainment)",
    "media tuner": "Media / Tuner (Entertainment)",
    "media/tuner": "Media / Tuner (Entertainment)",
    "tuner": "Media / Tuner (Entertainment)",
    "radio": "Media / Tuner (Entertainment)",
    "audio": "Media / Tuner (Entertainment)",
    "music": "Media / Tuner (Entertainment)",
    "entertainment": "Media / Tuner (Entertainment)",
    "infotainment": "Media / Tuner (Entertainment)",
    "streaming": "Media / Tuner (Entertainment)",
    "spotify": "Media / Tuner (Entertainment)",
    "am fm": "Media / Tuner (Entertainment)",
    "am/fm": "Media / Tuner (Entertainment)",
    "dab": "Media / Tuner (Entertainment)",
    "digital radio": "Media / Tuner (Entertainment)",
    "satellite radio": "Media / Tuner (Entertainment)",
    "sirius": "Media / Tuner (Entertainment)",
    "xm": "Media / Tuner (Entertainment)",
    "podcast": "Media / Tuner (Entertainment)",
    "podcasts": "Media / Tuner (Entertainment)",
    "sound": "Media / Tuner (Entertainment)",
    "speaker": "Media / Tuner (Entertainment)",
    "speakers": "Media / Tuner (Entertainment)",
    "surround sound": "Media / Tuner (Entertainment)",
    "bose": "Media / Tuner (Entertainment)",
    "burmester": "Media / Tuner (Entertainment)",
    "playback": "Media / Tuner (Entertainment)",
    "player": "Media / Tuner (Entertainment)",
    "cd": "Media / Tuner (Entertainment)",
    "dvd": "Media / Tuner (Entertainment)",

    # App Store / 3rd Party
    "app store": "App Store / 3rd Party",
    "appstore": "App Store / 3rd Party",
    "apps store": "App Store / 3rd Party",
    "third party": "App Store / 3rd Party",
    "3rd party": "App Store / 3rd Party",
    "third-party": "App Store / 3rd Party",
    "3rd-party": "App Store / 3rd Party",
    "3p": "App Store / 3rd Party",
    "external apps": "App Store / 3rd Party",
    "external": "App Store / 3rd Party",
    "marketplace": "App Store / 3rd Party",
    "store": "App Store / 3rd Party",
    "google play": "App Store / 3rd Party",
    "play store": "App Store / 3rd Party",
    "apple store": "App Store / 3rd Party",
    "ios apps": "App Store / 3rd Party",
    "android apps": "App Store / 3rd Party",
    "third party apps": "App Store / 3rd Party",
    "partner apps": "App Store / 3rd Party",
    "partner": "App Store / 3rd Party",
    "partners": "App Store / 3rd Party",
    "vendor apps": "App Store / 3rd Party",
    "vendor": "App Store / 3rd Party",
    "ota apps": "App Store / 3rd Party",

    # Digital Assistant
    "digital assistant": "Digital assistant",
    "digi assistant": "Digital assistant",
    "digi": "Digital assistant",
    "voice assistant": "Digital assistant",
    "assistant": "Digital assistant",
    "da": "Digital assistant",
    "voice": "Digital assistant",
    "speech": "Digital assistant",
    "speech recognition": "Digital assistant",
    "voice recognition": "Digital assistant",
    "voice control": "Digital assistant",
    "voice commands": "Digital assistant",
    "hey porsche": "Digital assistant",
    "hey car": "Digital assistant",
    "siri": "Digital assistant",
    "alexa": "Digital assistant",
    "google assistant": "Digital assistant",
    "cortana": "Digital assistant",
    "nlp": "Digital assistant",
    "natural language": "Digital assistant",
    "natural language processing": "Digital assistant",
    "voice search": "Digital assistant",
    "wake word": "Digital assistant",
    "hotword": "Digital assistant",
    "speech to text": "Digital assistant",
    "stt": "Digital assistant",
    "text to speech": "Digital assistant",
    "tts": "Digital assistant",
    "ai assistant": "Digital assistant",
    "virtual assistant": "Digital assistant",
}

PRODUCT_OWNERS = [
    "Hans Georg Wahl", "Deepak Illoth Veetil", "Elena Florez",
    "Martin Melle", "Regina Haeussermann",
]

METADATA = ["Total Scope", "Orphans", "Not Yet Planned", "Planned"]

def get_client(timeout=30):
    return httpx.Client(proxy=PROXY, timeout=timeout, verify=False)

def get_local_client(timeout=30):
    transport = httpx.HTTPTransport(proxy=None)
    return httpx.Client(
        timeout=timeout,
        verify=False,
        transport=transport,
        trust_env=False
    )

app = FastAPI(title="MLB TestPlan MCP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALIASES.update({
    # Metadata variants from HTML
    "total scope": "Total Scope",
    "total": "Total Scope",

    "orphans": "Orphans",
    "orphan": "Orphans",

    "planned": "Planned",
    "plan": "Planned",

    "not yet planned": "Not Yet Planned",
    "not yet in planned": "Not Yet Planned",
    "not planned": "Not Yet Planned",
})

STATUS_VALUES = {
    "PASS",
    "FAIL",
    "BLOCKED",
    "ABORTED",
    "ToDo",
    "Executing",
}

WORKSTREAM_VALUES = {
    "WS Applications",
    "WS Platform",
    "WS System",
}

METADATA_VALUES = {
    "Total Scope",
    "Orphans",
    "Not Yet Planned",
    "Planned",
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("_", " ")
    text = re.sub(r"[-/()\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_test_plan_key_from_confluence(filters: dict, debug: bool = False, page_id: str = None):
    """
    Fetch the Confluence SOP page and find the Test Plan key that matches the
    parsed filters (working_group + location).

    Strategy (cell-level, accurate):
    Pass 1 — Build a key→region map by finding cells that contain BOTH
              testPlanTests(KEY) and testExecutionTests('MIB4_SOP_TEs_REGION').
              This is 100% accurate because both tokens are in the same JQL cell.
    Pass 2 — Build a key→working_group map from header rows whose first cell
              contains the working group label.
    Then intersect: find the key whose (region, working_group) matches the filters.
    """
    try:
        _page_id = page_id or CONFLUENCE_PAGE_ID
        with get_local_client(timeout=15) as client:
            resp = client.get(f"{LOCAL_API_URL}/page/{_page_id}")
            if resp.status_code in (301, 302):
                resp = client.get(resp.headers.get("location", ""))
            if resp.status_code != 200:
                return None
            data = resp.json()

        body = data.get("body", "") or ""
        if not body:
            return None

        soup = BeautifulSoup(body, "html.parser")
        jira_pattern = re.compile(r"\b(MLBEVO-\d+)\b")
        region_cell_pattern = re.compile(
            r"testPlanTests\((MLBEVO-\d+)\).*?testExecutionTests\('MIB4_SOP_TEs_(\w+)'",
            re.IGNORECASE | re.DOTALL
        )
        wg_patterns = [
            # More specific patterns first — prevent WS Platform/System from
            # shadowing Phone-Connectivity when they share the same header row.
            ("Navigation",                   re.compile(r"Navigation", re.I)),
            ("Digital assistant",            re.compile(r"Digital\s+Assistant", re.I)),
            ("Phone-Connectivity-SPI",       re.compile(r"Phone.Connectivity|Phone-Connectivity|\[Phone", re.I)),
            ("Core HMI / GBK",               re.compile(r"Core\s+HMI|GBK", re.I)),
            ("Media / Tuner (Entertainment)",re.compile(r"Media.*Tuner|Tuner.*Media", re.I)),
            ("App Store / 3rd Party",        re.compile(r"App\s+Store|3rd\s+Party", re.I)),
            ("WS Applications",              re.compile(r"WS\s+Applic", re.I)),
            ("WS Platform",                  re.compile(r"WS\s+Platform", re.I)),
            ("WS System",                    re.compile(r"WS\s+System", re.I)),
            ("System Audio",                  re.compile(r"System\s+Audio|SystemAudio", re.I)),
            ("Car",                           re.compile(r"\bCar\b", re.I)),
            ("Sport Apps",                    re.compile(r"Sport\s+Apps?|Sports?\s+Apps?", re.I)),
        ]

        # Pass 1: build key → region map (cell-level accuracy)
        key_region: dict[str, str] = {}
        key_wg: dict[str, str] = {}
        for row in soup.find_all("tr"):
            for cell in row.find_all(["td", "th"]):
                cell_text = cell.get_text(" ", strip=True)
                m = region_cell_pattern.search(cell_text)
                if m:
                    key_region[m.group(1)] = m.group(2).upper()  # e.g. JPN, ECE, NAR

        # Fallback: column-based layout (page 2 format — regions as column headers)
        if not key_region:
            _REGION_COL_PATTERNS = [
                ("ECE",  re.compile(r"Testing\s+ECE",       re.I)),
                ("NAR",  re.compile(r"Testing\s+NAR",       re.I)),
                ("JPN",  re.compile(r"Testing\s+JPN",       re.I)),
                ("KOR",  re.compile(r"Testing\s+KOR",       re.I)),
                ("TWN",  re.compile(r"Testing\s+TWN",       re.I)),
                ("HKG",  re.compile(r"Testing\s+Hong.Kong", re.I)),
                ("MAC",  re.compile(r"Testing\s+Macau",     re.I)),
            ]
            _col2_wg_patterns = wg_patterns + [
                ("System Audio", re.compile(r"System\s*/?\s*\[?Audio\]?|SystemAudio", re.I)),
                ("Car",          re.compile(r"\bCar\b", re.I)),
                ("Sport Apps",   re.compile(r"Sport\s+Apps?|Sports?\s+Apps?", re.I)),
            ]
            # Find the main table that has region column headers.
            # Only iterate its DIRECT rows (recursive=False on tbody) to avoid
            # picking up keys from nested PASS/FAIL/BLOCKED sub-tables.
            main_table = None
            region_col_map: dict[int, str] = {}
            for tbl in soup.find_all("table"):
                first_row = tbl.find("tr")
                if not first_row:
                    continue
                headers = first_row.find_all(["th", "td"])
                tmp_map: dict[int, str] = {}
                for i, h in enumerate(headers):
                    h_text = h.get_text(" ", strip=True)
                    for token, pat in _REGION_COL_PATTERNS:
                        if pat.search(h_text):
                            tmp_map[i] = token
                            break
                if len(tmp_map) >= 3:  # must have at least 3 region columns
                    main_table = tbl
                    region_col_map = tmp_map
                    break

            if main_table and region_col_map:
                # Only direct <tr> children of the table / tbody — skips nested tables
                tbody = main_table.find("tbody") or main_table
                direct_rows = tbody.find_all("tr", recursive=False)
                header_cell_count = max(region_col_map.keys()) + 1  # e.g. 10
                current_wg2 = None
                for row in direct_rows:
                    # find_all with recursive=False gives only direct <td>/<th> of this row
                    cells = row.find_all(["td", "th"], recursive=False)
                    if not cells:
                        continue
                    # Rows with rowspan cells absent will have fewer cells → shift indices
                    offset = header_cell_count - len(cells)
                    adj_region_col_map = {
                        (idx - offset): token
                        for idx, token in region_col_map.items()
                        if (idx - offset) >= 0
                    }
                    # Detect working group from the WORKING GROUP column only
                    # Full row (offset=0): WG is col 1; rowspan row (offset=1): WG is col 0
                    detected_wg2 = None
                    wg_col_idx = max(0, 1 - offset)
                    if wg_col_idx < len(cells):
                        wg_cell_text = cells[wg_col_idx].get_text(" ", strip=True)
                        for wg_name, wg_re in _col2_wg_patterns:
                            if wg_re.search(wg_cell_text):
                                detected_wg2 = wg_name
                                break
                    if detected_wg2:
                        current_wg2 = detected_wg2
                    # Extract the FIRST MLBEVO key from each region column cell only
                    for col_idx, token in adj_region_col_map.items():
                        if col_idx >= len(cells):
                            continue
                        cell = cells[col_idx]
                        # Find <ac:parameter ac:name="key"> tag directly inside this cell
                        ac_key_tag = cell.find(
                            lambda t: t.name and "parameter" in t.name.lower()
                            and t.get("ac:name", "").lower() == "key"
                        )
                        if ac_key_tag:
                            k = ac_key_tag.get_text(strip=True)
                            if jira_pattern.match(k):
                                key_region[k] = token
                                if k not in key_wg and current_wg2:
                                    key_wg[k] = current_wg2

        # Pass 2: build key → working group map from header rows
        current_wg = None
        for row in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            if not cells:
                continue
            # Scan ALL cells for a working group pattern (not just first cell),
            # preferring more specific patterns (Phone-Connectivity over WS Platform).
            # wg_patterns is ordered from most-specific to least-specific.
            detected_wg = None
            for wg_name, wg_re in wg_patterns:
                for cell in cells:
                    if wg_re.search(cell):
                        detected_wg = wg_name
                        break
                if detected_wg:
                    break
            if detected_wg:
                current_wg = detected_wg
            # Assign current_wg to all keys in this row that don't have one yet
            if current_wg:
                for key in jira_pattern.findall(" ".join(cells)):
                    if key not in key_wg:
                        key_wg[key] = current_wg

        if debug:
            combined = []
            for key in set(list(key_region.keys()) + list(key_wg.keys())):
                combined.append({
                    "key": key,
                    "region": key_region.get(key, "?"),
                    "working_group": key_wg.get(key, "?"),
                })
            return sorted(combined, key=lambda x: (x["region"], x["key"]))

        # --- multi-match mode (used by /confluence/testplans) ---
        if filters.get("_return_all"):
            location = filters.get("location", "") or ""
            working_group = filters.get("working_group", "") or ""
            _LOCATION_TO_TOKEN_ALL = {
                "Testing ECE":       "ECE",
                "Testing NAR":       "NAR",
                "Testing JPN":       "JPN",
                "Testing KOR":       "KOR",
                "Testing TWN":       "TWN",
                "Testing Hong-Kong": "HKG",
                "Testing Macau":     "MAC",
            }
            _TOKEN_TO_LOCATION = {v: k for k, v in _LOCATION_TO_TOKEN_ALL.items()}
            location_token = _LOCATION_TO_TOKEN_ALL.get(location, "")
            matches = []
            for key in set(list(key_region.keys()) + list(key_wg.keys())):
                region_token = key_region.get(key, "")
                wg = key_wg.get(key, "")
                region_match = (not location_token) or (region_token == location_token)
                wg_match = (not working_group) or (
                    working_group.lower() in wg.lower()
                    or wg.lower() in working_group.lower()
                )
                if region_match and wg_match:
                    matches.append({
                        "test_plan_key": key,
                        "region": _TOKEN_TO_LOCATION.get(region_token, region_token),
                        "working_group": wg,
                    })
            matches.sort(key=lambda x: (x["region"], x["working_group"], x["test_plan_key"]))
            return matches

        # Match filters
        location = filters.get("location", "") or ""
        working_group = filters.get("working_group", "") or ""

        # Map canonical location names → Confluence MIB4_SOP_TEs_ region tokens
        _LOCATION_TO_TOKEN = {
            "Testing ECE":       "ECE",
            "Testing NAR":       "NAR",
            "Testing JPN":       "JPN",
            "Testing KOR":       "KOR",
            "Testing TWN":       "TWN",
            "Testing Hong-Kong": "HKG",
            "Testing Macau":     "MAC",
        }
        location_abbrev = _LOCATION_TO_TOKEN.get(location, location.strip().split()[-1].upper() if location.strip() else "")

        candidates = []
        for key, region in key_region.items():
            region_match = (not location_abbrev) or (region == location_abbrev)
            wg = key_wg.get(key, "")
            wg_match = (not working_group) or (working_group.lower() in wg.lower() or wg.lower() in working_group.lower())
            score = int(region_match) + int(wg_match)
            if score > 0:
                candidates.append((score, key, region, wg))

        if not candidates:
            return None

        # Sort by score desc, then key asc (deterministic)
        candidates.sort(key=lambda x: (-x[0], x[1]))
        return candidates[0][1]

    except Exception:
        return None


@app.get(
    "/parse-keywords",
    operation_id="parse_keywords",
    summary="Parse natural language into canonical filters",
)
def parse_keywords(prompt: str = Query(...)):
    normalized = normalize_text(prompt)

    result = {
        "raw_prompt": prompt,
        "workstream": None,
        "working_group": None,
        "product_owner": None,
        "location": None,
        "metadata": None,
        "status": None,
        "test_plan_key": None,
        "kpm_id": None,
        "free_text": [],
    }

    matched_spans = []

    sorted_aliases = sorted(
        ALIASES.items(),
        key=lambda x: len(normalize_text(x[0])),
        reverse=True,
    )

    for alias, canonical in sorted_aliases:
        alias_norm = normalize_text(alias)
        pattern = r"(?<!\w)" + re.escape(alias_norm) + r"(?!\w)"

        if not re.search(pattern, normalized):
            continue

        matched_spans.append(alias_norm)

        if canonical in WORKSTREAM_VALUES:
            if result["workstream"] is None:
                result["workstream"] = canonical
        elif canonical.startswith("Testing "):
            if result["location"] is None:
                result["location"] = canonical
        elif canonical in STATUS_VALUES:
            if result["status"] is None:
                result["status"] = canonical
        elif canonical in METADATA_VALUES:
            if result["metadata"] is None:
                result["metadata"] = canonical
        else:
            if result["working_group"] is None:
                result["working_group"] = canonical

    for owner in PRODUCT_OWNERS:
        owner_norm = normalize_text(owner)
        pattern = r"(?<!\w)" + re.escape(owner_norm) + r"(?!\w)"
        if re.search(pattern, normalized):
            result["product_owner"] = owner
            matched_spans.append(owner_norm)
            break

    m = re.search(r"\bKPM-\d+\b", prompt, re.IGNORECASE)
    if m:
        result["kpm_id"] = m.group(0).upper()

    jira = re.findall(r"\b[A-Z][A-Z0-9]+-\d+\b", prompt, re.IGNORECASE)
    for item in jira:
        if not item.upper().startswith("KPM-"):
            result["test_plan_key"] = item.upper()
            break

    cleaned = normalized
    for phrase in sorted(matched_spans, key=len, reverse=True):
        cleaned = re.sub(
            r"(?<!\w)" + re.escape(phrase) + r"(?!\w)",
            " ",
            cleaned,
        )

    if result["product_owner"]:
        cleaned = re.sub(
            re.escape(normalize_text(result["product_owner"])),
            " ",
            cleaned,
        )

    cleaned = re.sub(r"\bKPM-\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[A-Z][A-Z0-9]+-\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if cleaned:
        result["free_text"] = cleaned.split()

    # If no explicit Jira key was typed, resolve via the same path used by
    # /confluence/testplans (proven _return_all mode) and pick the best match.
    if not result["test_plan_key"]:
        _filters = {
            "location":      result.get("location") or "",
            "working_group": result.get("working_group") or "",
            "_return_all":   True,
        }
        _all_matches = []
        _seen = set()
        for _pid in [CONFLUENCE_PAGE_ID, "2381910576"]:
            for item in (_extract_test_plan_key_from_confluence(_filters, page_id=_pid) or []):
                k = item.get("test_plan_key")
                if k and k not in _seen:
                    _seen.add(k)
                    _all_matches.append(item)
        if _all_matches:
            result["test_plan_key"] = _all_matches[0]["test_plan_key"]

    return result


# All canonical regions and working groups (used by /testplans/expand)
_ALL_REGIONS = [
    "Testing ECE", "Testing NAR", "Testing JPN",
    "Testing KOR", "Testing TWN", "Testing Hong-Kong", "Testing Macau",
]
_ALL_WORKING_GROUPS = [
    "Navigation", "Digital assistant", "Phone-Connectivity-SPI",
    "Core HMI / GBK", "Media / Tuner (Entertainment)", "App Store / 3rd Party",
    "System Audio", "Car", "Sport Apps",
    "WS Applications", "WS Platform", "WS System",
]

@app.get(
    "/testplans/expand",
    operation_id="expand_testplans",
    summary="Expand a region OR working group to all matching test plan keys",
)
def expand_testplans(query: str = Query(..., description='e.g. "navigation" or "testing ece"')):
    """
    Given a region name OR working group name, returns all test plan keys found
    for every combination with the other dimension.

    Examples:
      query="navigation"   → returns NAV test plans across all regions
      query="testing ece"  → returns all working groups test plans for ECE
    """
    normalized = normalize_text(query)

    # Detect if the query resolves to a region or a working group
    matched_region = None
    matched_wg = None

    for alias, canonical in ALIASES.items():
        alias_norm = normalize_text(alias)
        if alias_norm == normalized or re.search(r"(?<!\w)" + re.escape(alias_norm) + r"(?!\w)", normalized):
            if canonical in _ALL_REGIONS:
                matched_region = canonical
                break
            if canonical in _ALL_WORKING_GROUPS:
                matched_wg = canonical
                break

    if not matched_region and not matched_wg:
        return {"error": f"Could not recognise '{query}' as a known region or working group.", "query": query}

    page_ids = [CONFLUENCE_PAGE_ID, "2381910576"]
    results = []
    seen = set()

    if matched_region:
        mode  = "region"
        label = matched_region
        # Single call with only the region filter — no WG filter.
        # Keys with no WG assigned would falsely match every WG filter if we looped,
        # so we fetch all ECE keys at once and let key_wg determine their groups.
        filters = {"location": matched_region, "_return_all": True}
    else:
        mode  = "working_group"
        label = matched_wg
        # Single call with only the WG filter — no region filter.
        filters = {"working_group": matched_wg, "_return_all": True}

    for pid in page_ids:
        matches = _extract_test_plan_key_from_confluence(filters, page_id=pid) or []
        for m in matches:
            k = m.get("test_plan_key")
            wg = m.get("working_group", "") or ""
            reg = m.get("region", "") or ""
            # Skip entries with no working_group when expanding by region,
            # and no region when expanding by working_group — they are unclassified.
            if mode == "region" and not wg:
                continue
            if mode == "working_group" and not reg:
                continue
            if k and k not in seen:
                seen.add(k)
                results.append({
                    "test_plan_key": k,
                    "region":        reg,
                    "working_group": wg,
                })

    # Group results
    grouped: dict[str, list] = {}
    group_field = "working_group" if mode == "region" else "region"
    for r in results:
        grp = r.get(group_field) or "Unknown"
        grouped.setdefault(grp, []).append(r["test_plan_key"])

    return {
        "query": query,
        "matched_as": mode,
        "label": label,
        "total_found": len(results),
        "grouped": grouped,
        "all": results,
    }


@app.get(
    "/parse-keywords/debug",
    operation_id="parse_keywords_debug",
    summary="Debug: show Confluence row scores for a prompt",
)
def parse_keywords_debug(prompt: str = Query(...)):
    """Returns the scored Confluence rows so you can see why a particular key was chosen."""
    # Re-run keyword parse without the Confluence lookup
    kw_result = parse_keywords.__wrapped__(prompt) if hasattr(parse_keywords, "__wrapped__") else None

    # Build filters directly
    normalized = normalize_text(prompt)
    temp_result = {
        "workstream": None, "working_group": None, "product_owner": None,
        "location": None, "metadata": None, "status": None,
    }
    sorted_aliases = sorted(ALIASES.items(), key=lambda x: len(normalize_text(x[0])), reverse=True)
    for alias, canonical in sorted_aliases:
        alias_norm = normalize_text(alias)
        if not re.search(r"(?<!\w)" + re.escape(alias_norm) + r"(?!\w)", normalized):
            continue
        if canonical in WORKSTREAM_VALUES:
            if temp_result["workstream"] is None: temp_result["workstream"] = canonical
        elif canonical.startswith("Testing "):
            if temp_result["location"] is None: temp_result["location"] = canonical
        elif canonical in STATUS_VALUES:
            if temp_result["status"] is None: temp_result["status"] = canonical
        elif canonical in METADATA_VALUES:
            if temp_result["metadata"] is None: temp_result["metadata"] = canonical
        else:
            if temp_result["working_group"] is None: temp_result["working_group"] = canonical

    scored_rows = _extract_test_plan_key_from_confluence(temp_result, debug=True)
    return {
        "filters_used": temp_result,
        "top_scored_rows": scored_rows[:20] if scored_rows else [],
    }


@app.get(
    "/confluence/page/testplan-rows",
    operation_id="confluence_testplan_rows",
    summary="Debug: dump all Confluence table rows that contain a Jira key",
)
def confluence_testplan_rows():
    """Returns every table row from the Confluence SOP that contains at least one Jira key,
    with the raw text so you can see exactly what fields are present."""
    try:
        with get_local_client(timeout=15) as client:
            resp = client.get(f"{LOCAL_API_URL}/page/{CONFLUENCE_PAGE_ID}")
            if resp.status_code in (301, 302):
                resp = client.get(resp.headers.get("location", ""))
            resp.raise_for_status()
            data = resp.json()

        body = data.get("body", "") or ""
        soup = BeautifulSoup(body, "html.parser")
        jira_pattern = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")

        rows_out = []
        for row in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            row_text = " | ".join(cells)
            keys = jira_pattern.findall(row_text)
            if keys:
                rows_out.append({"jira_keys": keys, "cells": cells, "row_text": row_text})

        return {"total_rows_with_keys": len(rows_out), "rows": rows_out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -- Tool: Fetch all matching test plans from Confluence -----------------------

_CANONICAL_REGIONS = {
    "Testing ECE", "Testing NAR", "Testing JPN", "Testing KOR",
    "Testing TWN", "Testing Hong-Kong", "Testing Macau",
}

_CANONICAL_WGS = {
    "Navigation", "Phone-Connectivity-SPI", "Core HMI / GBK",
    "Media / Tuner (Entertainment)", "App Store / 3rd Party", "Digital assistant",
}


def _resolve_filter(raw: str, target_set: set) -> str:
    """Normalize a raw user string to a canonical value using ALIASES, then
    verify it belongs to *target_set*.  Returns the canonical value or ''."""
    if not raw:
        return ""
    norm = normalize_text(raw)
    # Try alias lookup (longest first to prefer more specific matches)
    for alias, canonical in sorted(ALIASES.items(), key=lambda x: len(normalize_text(x[0])), reverse=True):
        if normalize_text(alias) == norm and canonical in target_set:
            return canonical
    # Direct case-insensitive match against the target set
    for value in target_set:
        if value.lower() == raw.strip().lower():
            return value
    return ""


@app.get(
    "/confluence/testplans",
    operation_id="get_confluence_testplans",
    summary="Fetch all test plans from Confluence for a Working Group and/or Region",
)
def get_confluence_testplans(
    working_group: str = Query(default="", description="Working Group name or synonym (e.g. 'navigation', 'hmi', 'bluetooth')"),
    region: str = Query(default="", description="Region name or synonym (e.g. 'japan', 'ece', 'north america')"),
    page_id: str = Query(default="", description="Optional: query a single Confluence page ID instead of merging both pages"),
):
    """
    Fetch all test plans from the Confluence SOP page that match the given
    Working Group and/or Region.

    - Synonyms are normalised using the ALIASES table before searching.
    - If only a Working Group is supplied → return test plans for all regions.
    - If only a Region is supplied → return test plans for all working groups.
    - If both are supplied → return only the exact intersection.
    - If neither is supplied → return every test plan found on the page.
    """
    canonical_wg = _resolve_filter(working_group, _CANONICAL_WGS)
    canonical_region = _resolve_filter(region, _CANONICAL_REGIONS)

    # Warn the caller when a non-empty input couldn't be resolved
    unresolved = []
    if working_group.strip() and not canonical_wg:
        unresolved.append(f"working_group='{working_group}'")
    if region.strip() and not canonical_region:
        unresolved.append(f"region='{region}'")

    if unresolved:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Could not resolve {', '.join(unresolved)} to a known value. "
                f"Valid Working Groups: {sorted(_CANONICAL_WGS)}. "
                f"Valid Regions: {sorted(_CANONICAL_REGIONS)}."
            ),
        )

    filters = {
        "location": canonical_region,
        "working_group": canonical_wg,
        "_return_all": True,
    }

    _CONFLUENCE_PAGE_IDS = [page_id] if page_id else [CONFLUENCE_PAGE_ID, "2381910576"]

    seen_keys: set = set()
    matches: list = []
    for _pid in _CONFLUENCE_PAGE_IDS:   
        _results = _extract_test_plan_key_from_confluence(filters, page_id=_pid) or []
        for item in _results:
            key = item.get("test_plan_key")
            if key and key not in seen_keys:
                seen_keys.add(key)
                matches.append(item)

    return {
        "filters": {
            "working_group_raw": working_group or None,
            "working_group_canonical": canonical_wg or None,
            "region_raw": region or None,
            "region_canonical": canonical_region or None,
        },
        "total": len(matches),
        "test_plans": matches,
        "message": None if matches else "No test plans found for the given filters.",
    }


# -- Tool 2: Confluence page ---------------------------------------------------

@app.get("/confluence/page/{page_id}", operation_id="get_confluence_page",
         summary="Step 2: Retrieve Test Plan SOP page from Confluence")
def get_confluence_page(page_id: str = CONFLUENCE_PAGE_ID):
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{LOCAL_API_URL}/page/{page_id}")
        if resp.status_code in (301, 302):
            redirect_url = resp.headers.get("location")
            resp = client.get(redirect_url)
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "space": data.get("space"),
            "version": data.get("version"),
            "body": data.get("body"),
            "url": data.get("url"),
        }


# -- Tool 3: Get failed tests --------------------------------------------------

@app.get("/testplan/{test_plan_key}/failed-tests", operation_id="get_failed_tests",
         summary="Step 3: Get all tests with latestStatus=FAIL from Xray")
def get_failed_tests(test_plan_key: str):
    all_tests = []
    with get_local_client(timeout=60) as client:
        for page in range(1, 20):
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/testplan/{test_plan_key}/tests",
                params={"page": page, "limit": 100}
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = next(
                    (data[k] for k in ("tests","testExecutions","data","results","items")
                     if isinstance(data.get(k), list)), []
                )
            else:
                items = []
            if not items:
                break
            all_tests.extend(items)
            if len(items) < 100:
                break

    def get_status(item):
        status = item.get("latestStatus") or item.get("status")
        if isinstance(status, str):
            return status.upper()
        if isinstance(status, dict):
            return (status.get("name") or status.get("value") or status.get("key") or "").upper()
        return ""

    def get_key(item):
        return (
            item.get("testKey") or item.get("key") or item.get("issueKey")
            or (item.get("test") or {}).get("key")
            or (item.get("test") or {}).get("testKey")
        )

    failed = [t for t in all_tests if get_status(t) == "FAIL"]
    return {
        "test_plan_key": test_plan_key,
        "total_fetched": len(all_tests),
        "total_failed": len(failed),
        "failed_keys": [get_key(t) for t in failed],
        "failed_tests": failed,
    }


# -- Tool 4: Get test executions -----------------------------------------------

@app.get("/testplan/{test_plan_key}/executions", operation_id="get_test_plan_executions",
         summary="Step 4: Get all Test Execution keys linked to a Test Plan")
def get_test_plan_executions(test_plan_key: str):
    all_executions = []
    with get_local_client(timeout=60) as client:
        for page in range(1, 20):
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/testplan/{test_plan_key}/testexecutions",
                params={"page": page, "limit": 100}
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = next(
                    (data[k] for k in ("tests","testExecutions","data","results","items")
                     if isinstance(data.get(k), list)), []
                )
            else:
                items = []
            if not items:
                break
            all_executions.extend(items)
            if len(items) < 100:
                break

    exec_keys = [
        item.get("key") or item.get("testExecKey") or item.get("testExecutionKey")
        for item in all_executions
    ]
    return {
        "test_plan_key": test_plan_key,
        "total_executions": len(all_executions),
        "execution_keys": [k for k in exec_keys if k],
    }


# -- Tool 5: Map failed test keys to run IDs -----------------------------------
@app.get("/testplan/{test_plan_key}/map-failed-runs", operation_id="map_failed_runs",
         summary="Step 5: Paginate all test runs and map failed test keys to run IDs")
def map_failed_runs(test_plan_key: str):
    failed_result = get_failed_tests(test_plan_key)
    failed_keys = set(failed_result["failed_keys"])

    if not failed_keys:
        return {
            "message": "No FAIL tests found.",
            "test_plan_key": test_plan_key
        }

    run_map = {}

    with get_local_client(timeout=60) as client:
        for page in range(1, 20):
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/testruns",
                params={
                    "testPlanKey": test_plan_key,
                    "page": page,
                    "limit": 100,
                },
            )

            if resp.status_code != 200:
                break

            data = resp.json()

            if isinstance(data, list):
                runs = data
            elif isinstance(data, dict):
                runs = next(
                    (
                        data[k]
                        for k in ("tests", "testExecutions", "data", "results", "items")
                        if isinstance(data.get(k), list)
                    ),
                    [],
                )
            else:
                runs = []

            # Stop only when there are no more runs
            if not runs:
                break

            for run in runs:
                test_key = (
                    run.get("testKey")
                    or run.get("key")
                    or run.get("issueKey")
                    or (run.get("test") or {}).get("key")
                )

                status = run.get("status")
                if isinstance(status, dict):
                    status = (
                        status.get("name")
                        or status.get("value")
                        or status.get("key")
                    )

                if test_key in failed_keys and status == "FAIL":
                    run_id = run.get("id")
                    existing = run_map.get(test_key)

                    # Keep the latest FAIL run (highest run_id)
                    if not existing or (
                        run_id and run_id > (existing.get("run_id") or 0)
                    ):
                        run_map[test_key] = {
                            "run_id": run_id,
                            "test_exec_key": (
                                run.get("testExecKey")
                                or run.get("testExecutionKey")
                            ),
                            "status": status,
                        }

            # Don't stop on partial pages.
            # Continue until the API returns an empty page.

    unique_test_exec_keys = list(
        {
            data["test_exec_key"]
            for data in run_map.values()
            if data.get("test_exec_key")
        }
    )

    return {
        "test_plan_key": test_plan_key,
        "total_failed": len(failed_keys),
        "mapped": len(run_map),
        "run_map": run_map,
        "test_exec_keys": unique_test_exec_keys,
        "test_exec_key_count": len(unique_test_exec_keys),
    }


# -- Tool 6: Analyze failed tests with KPMs ------------------------------------

@app.get("/testplan/{test_plan_key}/analyze", operation_id="analyze_failed_tests_with_kpms",
         summary="Steps 3-6 combined: all FAILs → executions → run IDs → KPM comments")
def analyze_failed_tests_with_kpms(test_plan_key: str):
    try:
        failed_result = get_failed_tests(test_plan_key)
        failed_keys = set(failed_result["failed_keys"])
        if not failed_keys:
            return {"message": "No FAIL tests found.", "test_plan_key": test_plan_key}

        run_map = {}
        with get_local_client(timeout=60) as client:
            for page in range(1, 20):
                resp = client.get(
                    f"{XRAY_BASE_URL}/xray/testruns",
                    params={"testPlanKey": test_plan_key, "page": page, "limit": 100}
                )
                if resp.status_code != 200:
                    break
                data = resp.json()
                if isinstance(data, list):
                    runs = data
                elif isinstance(data, dict):
                    runs = next(
                        (data[k] for k in ("tests","testExecutions","data","results","items")
                         if isinstance(data.get(k), list)), []
                    )
                else:
                    runs = []
                if not runs:
                    break
                for run in runs:
                    test_key = (
                        run.get("testKey") or run.get("key") or run.get("issueKey")
                        or (run.get("test") or {}).get("key")
                    )
                    if test_key in failed_keys and test_key not in run_map:
                        run_map[test_key] = {
                            "run_id": run.get("id"),
                            "test_exec_key": run.get("testExecKey") or run.get("testExecutionKey"),
                        }
                if len(runs) < 100:
                    break

        results = []
        errors = []
        with get_local_client(timeout=30) as client:
            for test_key, run_info in run_map.items():
                run_id = run_info.get("run_id")
                if not run_id:
                    errors.append({"test_key": test_key, "error": "No run_id found"})
                    continue
                try:
                    resp = client.get(f"{XRAY_BASE_URL}/xray/testrun/{run_id}")
                    resp.raise_for_status()
                    detail = resp.json()

                    comment = detail.get("comment")
                    if isinstance(comment, dict):
                        comment = comment.get("value") or comment.get("text") or ""
                    comment = comment or ""

                    status = detail.get("status")
                    if isinstance(status, dict):
                        status = status.get("name") or status.get("value") or status.get("key")

                    kpm_ids = []
                    for pattern in [
                        r"KPM[:\s#-]+(\d+)",
                        r"KPM Problem\s*-\s*(\d+)",
                        r"kpmweb[^\s]*id=(\d+)",
                        r"\bKPM-(\d+)\b",
                    ]:
                        kpm_ids.extend(re.findall(pattern, comment, re.IGNORECASE))

                    results.append({
                        "test_key": test_key,
                        "run_id": run_id,
                        "test_exec_key": run_info.get("test_exec_key"),
                        "status": status,
                        "comment": comment,
                        "kpm_ids": list(set(kpm_ids)),
                    })
                except Exception as e:
                    errors.append({"test_key": test_key, "run_id": run_id, "error": str(e)})

        kpm_summary = {}
        for r in results:
            for kpm in r.get("kpm_ids", []):
                kpm_summary.setdefault(kpm, []).append(r["test_key"])

        return {
            "test_plan_key": test_plan_key,
            "total_failed": len(failed_keys),
            "total_mapped": len(run_map),
            "results": results,
            "errors": errors,
            "kpm_summary": kpm_summary,
        }

    except Exception as e:
        return {"error": f"Pipeline failed: {str(e)}", "test_plan_key": test_plan_key}


# -- Tool 7: Get KPM comments using Test Execution Key + Test Key --------------

@app.get(
    "/testplan/{test_plan_key}/kpm-comments",
    operation_id="get_failed_test_kpm_comments",
    summary="Get KPM comments for all failed tests using testExecIssueKey + testIssueKey",
)
def get_failed_test_kpm_comments(test_plan_key: str):
    try:
        mapping = map_failed_runs(test_plan_key)

        run_map = mapping.get("run_map", {})
        if not run_map:
            return {
                "test_plan_key": test_plan_key,
                "message": "No failed tests found.",
                "results": [],
            }

        results = []
        errors = []

        with get_local_client(timeout=30) as client:
            for test_key, info in run_map.items():
                test_exec_key = info.get("test_exec_key")
                if not test_exec_key:
                    errors.append({"test_key": test_key, "error": "Missing test_exec_key"})
                    continue

                try:
                    resp = client.get(
                        f"{XRAY_BASE_URL}/xray/testrun",
                        params={
                            "testExecIssueKey": test_exec_key,
                            "testIssueKey": test_key,
                        },
                    )
                    resp.raise_for_status()
                    detail = resp.json()

                    status = detail.get("status")
                    if isinstance(status, dict):
                        status = (
                            status.get("name")
                            or status.get("value")
                            or status.get("key")
                        )

                    comment = detail.get("comment", "")
                    if isinstance(comment, dict):
                        comment = (
                            comment.get("value")
                            or comment.get("text")
                            or ""
                        )
                    comment = str(comment).strip()

                    # Extract all 8-digit KPM ticket numbers
                    kpm_ids = re.findall(r"(?<!\d)(\d{8})(?!\d)", comment)
                    kpm_ids = list(dict.fromkeys(kpm_ids))

                    results.append({
                        "test_key": test_key,
                        "test_exec_key": test_exec_key,
                        "status": status,
                        "comment": comment,
                        "comment_length": len(comment),
                        "kpm_ids": kpm_ids,
                    })

                except Exception as e:
                    errors.append({
                        "test_key": test_key,
                        "test_exec_key": test_exec_key,
                        "error": str(e),
                    })

        # Build after the loop so it reflects all results
        test_exec_comments = [
            {
                "test_exec_key": r["test_exec_key"],
                "comment": r["comment"],
                "kpm_ids": r["kpm_ids"],
            }
            for r in results
            if r["comment"]
        ]

        return {
            "test_plan_key": test_plan_key,
            "total_failed": mapping.get("total_failed", 0),
            "total_checked": len(results),
            "test_exec_comments": test_exec_comments,
            "results": results,
            "errors": errors,
        }

    except Exception as e:
        return {
            "test_plan_key": test_plan_key,
            "error": str(e),
        }


# -- Tool 8: FAIL report (Test Plan or single Test) ----------------------------

# def _extract_kpm(text: str) -> Optional[str]:
#     """Extract first KPM ID found in a text string."""
#     if not text:
#         return None
#     for pattern in _KPM_PATTERNS:
#         match = pattern.search(text)
#         if match:
#             return match.group(1)
#     return None
_KPM_REGEX = re.compile(r"(?<!\d)(1\d{7})(?!\d)")

def _extract_kpm(text: str) -> Optional[str]:
    if not text:
        return None
    match = _KPM_REGEX.search(str(text))
    return match.group(1) if match else None

def _normalize_text(value) -> str:
    if isinstance(value, dict):
        return (
            value.get("raw")
            or value.get("rendered")
            or value.get("value")
            or value.get("text")
            or ""
        )
    return str(value or "").strip()

def _get_kpm_from_run(run: dict) -> Optional[str]:
    if not run:
        return None

    # 1. PRIMARY SOURCE (same as Tool 7 behavior)
    comment = _normalize_text(run.get("comment"))
    kpm = _extract_kpm(comment)
    if kpm:
        return kpm

    # 2. FALLBACK: steps (only if needed)
    for step in run.get("steps") or []:
        actual = step.get("actualResult") or {}
        actual = _normalize_text(actual)

        kpm = _extract_kpm(actual)
        if kpm:
            return kpm

    return None


def _extract_items(data) -> list:
    """Normalize paginated response to a list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return next(
            (data[k] for k in ("tests", "testExecutions", "data", "results", "items")
             if isinstance(data.get(k), list)), []
        )
    return []


def _paginate_parallel(
    url: str,
    base_params: dict,
    client: httpx.Client,
    max_pages: int = _MAX_PAGES,
    stop_on_empty_only: bool = False,
) -> list:
    """Fetch paginated API data without speculative page requests.

    Despite the retained name for compatibility, pages are intentionally read
    sequentially through one pooled client. The Xray testruns endpoint ignores
    ``limit=100`` and currently returns 300 records per page; prefetching pages
    2..20 therefore creates an expensive Jira request storm when only two pages
    are needed. Independent per-item requests remain parallelized elsewhere.

    ``stop_on_empty_only`` preserves endpoints where a partial page does not
    reliably indicate the end of the result set.
    """
    all_items: list = []
    for page_num in range(1, max_pages + 1):
        resp = client.get(
            url,
            params={**base_params, "page": page_num, "limit": 100},
        )
        if resp.status_code != 200:
            break

        items = _extract_items(resp.json())
        if not items:
            break

        all_items.extend(items)
        if not stop_on_empty_only and len(items) < 100:
            break

    return all_items


def _fetch_issue_summary(test_key: str, client: Optional[httpx.Client] = None) -> str:
    """Fetch the Jira issue summary for *test_key*.

    Accepts an optional shared httpx.Client so callers can reuse a single
    connection pool across many concurrent fetches instead of opening a new
    TCP/TLS handshake per call.
    """
    owns_client = client is None
    try:
        if owns_client:
            client = get_local_client(timeout=30)
        resp = client.get(
            f"{XRAY_BASE_URL}/issue/{test_key}",
            follow_redirects=True,
        )
        if resp.status_code in (301, 302):
            resp = client.get(resp.headers["location"])
        if "application/json" not in resp.headers.get("content-type", ""):
            return ""
        issue = resp.json()
        return (
            issue.get("summary")
            or issue.get("fields", {}).get("summary")
            or ""
        )
    except Exception:
        return ""
    finally:
        if owns_client and client is not None:
            client.close()


def _fetch_issue_summaries(test_keys) -> dict[str, str]:
    """Fetch Jira issue summaries in JQL batches with per-key fallback.

    Jira's ``/search_issues`` proxy returns the same key/summary values as the
    individual ``/issue/{key}`` endpoint. Batching avoids one expensive Jira
    round trip per failed test while the fallback preserves existing behavior
    if a batch is rejected or returns an incomplete result.
    """
    keys = sorted({str(key).strip() for key in test_keys if str(key).strip()})
    summaries: dict[str, str] = {}
    if not keys:
        return summaries

    with get_local_client(timeout=60) as client:
        # Keep JQL URLs bounded for unusually large reports.
        for start in range(0, len(keys), 100):
            chunk = keys[start:start + 100]
            jql = f"key in ({','.join(chunk)})"
            try:
                resp = client.get(
                    f"{XRAY_BASE_URL}/search_issues",
                    params={"jql": jql, "max_results": len(chunk)},
                )
                if resp.status_code == 200:
                    for issue in resp.json().get("issues", []):
                        key = str(issue.get("key") or "").strip()
                        if key:
                            summaries[key] = str(issue.get("summary") or "")
            except Exception:
                logger.warning("Batch summary fetch failed; using per-key fallback")

        missing = [key for key in keys if key not in summaries]
        if missing:
            with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(missing))) as pool:
                futures = {
                    pool.submit(_fetch_issue_summary, key, client): key
                    for key in missing
                }
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        summaries[key] = future.result()
                    except Exception:
                        summaries[key] = ""

    return summaries


def _get_fail_runs_for_test_plan(test_plan_key: str) -> list[dict]:
    """
    For a Test Plan:
      1. Fetch all tests with latestStatus=FAIL via /xray/testplan/{key}/tests
      2. Paginate /xray/testruns to map FAIL test keys → run_id + exec_key
      3. Fetch each run detail in parallel to extract KPM + comment
    """
    # Step 1 — get failed test keys
    failed_result = get_failed_tests(test_plan_key)
    fail_keys = set(failed_result.get("failed_keys") or [])

    if not fail_keys:
        return []

    # Step 2 — fetch summaries AND paginate testruns in parallel.
    # Both are independent I/O operations, so overlapping them cuts wait time
    # roughly in half compared to running them sequentially.

    def _fetch_summaries() -> dict:
        return _fetch_issue_summaries(fail_keys)

    def _fetch_testruns() -> dict:
        rmap: dict[str, dict] = {}
        with get_local_client(timeout=60) as client:
            all_runs = _paginate_parallel(
                f"{XRAY_BASE_URL}/xray/testruns",
                {"testPlanKey": test_plan_key},
                client,
            )
        for run in all_runs:
            test_key = (
                run.get("testKey") or run.get("key") or run.get("issueKey")
                or (run.get("test") or {}).get("key")
            )
            status = run.get("status", "")
            if isinstance(status, dict):
                status = status.get("name") or status.get("value") or ""
            if test_key in fail_keys and "FAIL" in str(status).upper():
                run_id = run.get("id")
                existing = rmap.get(test_key)
                # keep newest run (higher id = newer in Xray in most setups)
                if not existing or (run_id and run_id > existing.get("run_id", 0)):
                    rmap[test_key] = {
                        "run_id": run_id,
                        "test_exec_key": run.get("testExecKey") or run.get("testExecutionKey"),
                        "status": status,
                        # The paginated object contains the same comment, steps,
                        # and KPM data as /xray/testrun/{id}; verified against
                        # all latest FAIL runs for MLBEVO-17818.
                        "_run_detail": run,
                    }
        return rmap

    # The local Jira proxy performs synchronous upstream work. Running these
    # bulk operations concurrently only adds contention; sequence them while
    # retaining connection pooling inside each operation.
    issue_summaries = _fetch_summaries()
    run_map = _fetch_testruns()

    return _build_results(run_map, issue_summaries)


def _get_fail_runs_for_test(test_key: str) -> list[dict]:
    """
    For a single Test issue:
      1. Fetch all execution keys via /xray/test/{key}/testexecutions
      2. For each execution, GET /xray/testrun
      3. Filter FAIL runs and extract KPM + comment in parallel
    """

    # -----------------------------
    # Step 1: collect execution keys (deduplicated)
    # -----------------------------
    execution_keys = set()

    with get_local_client(timeout=60) as client:
        for page in range(1, _MAX_PAGES + 1):
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/test/{test_key}/testexecutions",
                params={"page": page, "limit": 100},
            )

            if resp.status_code != 200:
                break

            items = _extract_items(resp.json())
            if not items:
                break

            for item in items:
                key = (
                    item.get("key")
                    or item.get("testExecKey")
                    or item.get("testExecutionKey")
                )
                if key:
                    execution_keys.add(key)

            if len(items) < 100:
                break

    if not execution_keys:
        return []

    issue_summaries = {test_key: ""}

    # -----------------------------
    # Step 2: fetch FAIL runs per execution
    # -----------------------------
    run_map = {}

    def _fetch_run_for_exec(exec_key: str):
        with get_local_client(timeout=30) as client:
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/testrun",
                params={
                    "testExecIssueKey": exec_key,
                    "testIssueKey": test_key,
                },
            )

            if resp.status_code != 200:
                return None, exec_key

            return resp.json(), exec_key

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {
            pool.submit(_fetch_run_for_exec, exec_key): exec_key
            for exec_key in execution_keys
        }

        for future in as_completed(futures):
            try:
                run, exec_key = future.result()
            except Exception:
                continue

            if not run:
                continue

            status = run.get("status", "")
            if isinstance(status, dict):
                status = (
                    status.get("name")
                    or status.get("value")
                    or status.get("key")
                    or ""
                )

            if str(status).upper() != "FAIL":
                continue

            run_id = run.get("id")

            # -----------------------------
            # FIX: key by exec_key (NOT test_key)
            # -----------------------------
            existing = run_map.get(exec_key)

            if not existing or (run_id and run_id > existing.get("run_id", 0)):
                run_map[exec_key] = {
                    "run_id": run_id,
                    "test_exec_key": exec_key,
                    "status": "FAIL",
                    "_run_detail": run,
                }

    # -----------------------------
    # Step 3: build final results
    # -----------------------------
    return _build_results(run_map, issue_summaries)

_EMPTY_ASSIGNEE = {
    "name": None,
    "displayName": None,
    "emailAddress": None,
    "accountId": None,
}


def _fetch_exec_assignee(test_exec_key: str, client: Optional[httpx.Client] = None) -> dict:
    """Fetch Test Execution issue details to extract assignee info.

    Accepts an optional shared httpx.Client so callers can reuse a single
    connection pool across many concurrent fetches instead of opening a new
    TCP/TLS connection per call.
    """
    if not test_exec_key:
        return dict(_EMPTY_ASSIGNEE)

    owns_client = client is None
    try:
        if owns_client:
            client = get_local_client(timeout=30)
        resp = client.get(
            f"{XRAY_BASE_URL}/issue/{test_exec_key}",
            follow_redirects=True,
        )
        resp.raise_for_status()

        issue = resp.json()

        # Adjust this path if your API returns assignee elsewhere
        assignee = (
            issue.get("assignee")
            or (issue.get("fields") or {}).get("assignee")
        )

        if assignee:
            return {
                "name": assignee.get("name"),
                "displayName": assignee.get("displayName"),
                "emailAddress": assignee.get("emailAddress"),
                "accountId": assignee.get("accountId"),
            }

    except Exception as e:
        logger.warning(
            f"Failed to fetch assignee for {test_exec_key}: {e}"
        )
    finally:
        if owns_client and client is not None:
            client.close()

    return dict(_EMPTY_ASSIGNEE)


def _build_results(run_map: dict, issue_summaries: dict) -> list[dict]:
    """
    Fetch full run details + assignee info in parallel and extract KPM ID + comment.

    Optimizations:
    - A single shared httpx.Client is reused across all worker threads (connection pooling).
    - Run detail fetches and assignee fetches are submitted into ONE thread pool
      together so both types of I/O run concurrently without per-item overhead.
    - Assignee results are cached by exec key to avoid duplicate fetches.
    - If _run_detail is already attached (single-test flow), that fetch is skipped.
    """
    results = []

    # Pre-compute unique exec keys to deduplicate assignee fetches.
    unique_exec_keys = {
        run_info.get("test_exec_key")
        for run_info in run_map.values()
        if run_info.get("test_exec_key")
    }

    with get_local_client(timeout=60) as client:
        assignee_cache: dict = {}
        run_details: dict = {}  # test_key → run detail dict

        # Submit ALL work — assignee fetches + run detail fetches — into one pool.
        # This means both types of requests are in-flight simultaneously.
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
            assignee_futs = {
                pool.submit(_fetch_exec_assignee, key, client): ("assignee", key)
                for key in unique_exec_keys
            }
            detail_futs = {
                pool.submit(
                    lambda tk=test_key, ri=run_info: (
                        ri.pop("_run_detail", None)
                        or (
                            client.get(f"{XRAY_BASE_URL}/xray/testrun/{ri['run_id']}").json()
                            if ri.get("run_id") and not ri.get("_run_detail")
                            else {}
                        )
                    )
                ): ("detail", test_key)
                for test_key, run_info in run_map.items()
            }

            all_futs = {**assignee_futs, **detail_futs}
            for fut in as_completed(all_futs):
                kind, key = all_futs[fut]
                try:
                    val = fut.result()
                except Exception:
                    val = dict(_EMPTY_ASSIGNEE) if kind == "assignee" else {}
                if kind == "assignee":
                    assignee_cache[key] = val
                else:
                    run_details[key] = val

        for test_key, run_info in run_map.items():
            run_detail = run_details.get(test_key) or {}
            kpm = _get_kpm_from_run(run_detail) if run_detail else None

            comment = ""
            if run_detail:
                raw_comment = run_detail.get("comment") or ""
                if isinstance(raw_comment, dict):
                    raw_comment = raw_comment.get("raw") or raw_comment.get("rendered") or ""
                comment = str(raw_comment).strip()

            # Extract last execution timestamp from raw Xray run object.
            # Xray Server/DC uses finishedOn (ISO-8601). Fall back to startedOn.
            executed_on = ""
            if run_detail:
                raw_ts = (
                    run_detail.get("finishedOn")
                    or run_detail.get("startedOn")
                    or run_detail.get("executedOn")
                    or run_detail.get("finishDate")
                    or run_detail.get("startDate")
                    or ""
                )
                if not isinstance(raw_ts, dict):
                    executed_on = str(raw_ts).strip()

            exec_key = run_info.get("test_exec_key")
            assignee = assignee_cache.get(exec_key, dict(_EMPTY_ASSIGNEE))

            results.append({
                "test_key": test_key,
                "summary": issue_summaries.get(test_key, ""),
                "test_exec_key": exec_key,
                "run_id": run_info.get("run_id"),
                "status": "FAIL",
                "executed_on": executed_on,
                "kpm_id": kpm or "No KPM",
                "comment": comment,
                "assignee": assignee,
            })

    results.sort(key=lambda r: r["test_key"])
    return results


@app.get(
    "/xray/fail-report/{issue_key}",
    operation_id="xray_get_fail_report",
    summary="Gets all FAIL test results with KPM IDs for a Test Plan or single Test",
)
def xray_get_fail_report(issue_key: str):
    """
    Retrieve all FAIL test results with KPM IDs for a given issue key.

    Handles two cases automatically:
    - Test Plan: paginates all test runs under the plan, fetches each FAIL run's
      details and extracts KPM ID.
    - Test (single): finds all Test Executions containing this test, fetches the
      run per execution, filters for FAIL, extracts KPM ID.
    """
    # Detect issue type via the Jira/Xray proxy (same host the other tools use).
    # The proxy returns a flat issue object where `issuetype` and `summary`
    # are top-level keys (it does NOT nest them under `fields`).
    start_time = time.perf_counter()
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{issue_key}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found.")
        resp.raise_for_status()
        issue_data = resp.json()

    raw_issue_type = (
        issue_data.get("issuetype")
        or (issue_data.get("fields") or {}).get("issuetype")
        or issue_data.get("issueType")
        or issue_data.get("type")
        or ""
    )
    if isinstance(raw_issue_type, dict):
        raw_issue_type = raw_issue_type.get("name") or raw_issue_type.get("value") or ""
    issue_type = str(raw_issue_type).strip().lower()

    summary = (
        issue_data.get("summary")
        or (issue_data.get("fields") or {}).get("summary", "")
        or ""
    )

    if issue_type == "test plan":
        fail_results = _get_fail_runs_for_test_plan(issue_key)
    elif issue_type == "test":
        fail_results = _get_fail_runs_for_test(issue_key)
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Issue {issue_key} is of type '{issue_type}'. "
                "Only 'Test Plan' and 'Test' issue types are supported."
            ),
        )

    kpm_count = sum(1 for r in fail_results if r["kpm_id"] != "No KPM")
    end_time = time.perf_counter()
    duration = int(round(end_time - start_time))

    return {
        "issue_key": issue_key,
        "issue_type": issue_type,
        "summary": summary,
        "total_fail": len(fail_results),
        "with_kpm": kpm_count,
        "without_kpm": len(fail_results) - kpm_count,
        "results": fail_results,
        "execution_time_seconds": duration
    }

# -- Helper: Historical FAIL scan (all runs, no JQL filter) --------------------

def _get_all_fail_runs_historical(test_plan_key: str) -> list[dict]:
    """
    Historical mode — scan ALL paginated runs and collect every unique test key
    that has EVER had a FAIL status (regardless of current latestStatus).
    Keeps the most recent FAIL run per test key (highest run_id).

    Optimization: the test-plan /tests pagination (previously used only to
    collect keys for summary fetches) is skipped entirely.  Summaries are
    fetched only for the FAIL keys found in testruns — a much smaller set —
    avoiding up to 2 000 sequential HTTP calls before any parallel work begins.
    """
    # Step 1 — scan ALL testruns, collect any FAIL (no pre-filter needed)
    run_map: dict[str, dict] = {}
    with get_local_client(timeout=60) as client:
        all_runs = _paginate_parallel(
            f"{XRAY_BASE_URL}/xray/testruns",
            {"testPlanKey": test_plan_key},
            client,
            stop_on_empty_only=True,  # xRay may return partial pages mid-pagination
        )
    for run in all_runs:
        test_key = (
            run.get("testKey") or run.get("key") or run.get("issueKey")
            or (run.get("test") or {}).get("key")
        )
        status = run.get("status", "")
        if isinstance(status, dict):
            status = status.get("name") or status.get("value") or ""
        if not test_key or "FAIL" not in str(status).upper():
            continue
        run_id = run.get("id")
        existing = run_map.get(test_key)
        if not existing or (run_id and run_id > (existing.get("run_id") or 0)):
            run_map[test_key] = {
                "run_id": run_id,
                "test_exec_key": run.get("testExecKey") or run.get("testExecutionKey"),
                "status": "FAIL",
                "_run_detail": run,
            }

    if not run_map:
        return []

    # Step 2 — fetch summaries only for the FAIL keys (batched JQL request)
    issue_summaries = _fetch_issue_summaries(run_map)

    return _build_results(run_map, issue_summaries)


# -- Tool: Historical FAIL report (Test Plan only) -----------------------------

@app.get(
    "/xray/fail-report/{issue_key}/historical",
    operation_id="xray_get_fail_report_historical",
    summary="Gets all historical FAIL results (including rerun tests) for a Test Plan",
)
def xray_get_fail_report_historical(issue_key: str):
    """
    Retrieve ALL tests that have EVER had a FAIL status in a Test Plan — including
    tests that were subsequently rerun and passed (excluded from the standard endpoint).

    Unlike the standard endpoint which uses latestStatus (current status only),
    this endpoint scans every raw test run across all pages.

    Use this when:
    - A Confluence snapshot shows more FAILs than the live endpoint returns
    - A test was FAIL but was rerun and reset to PASS/TODO
    - You need a complete audit trail of all failures
    """
    start_time = time.perf_counter()

    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{issue_key}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found.")
        resp.raise_for_status()
        issue_data = resp.json()

    raw_issue_type = (
        issue_data.get("issuetype")
        or (issue_data.get("fields") or {}).get("issuetype")
        or issue_data.get("issueType")
        or issue_data.get("type")
        or ""
    )
    if isinstance(raw_issue_type, dict):
        raw_issue_type = raw_issue_type.get("name") or raw_issue_type.get("value") or ""
    issue_type = str(raw_issue_type).strip().lower()

    summary = (
        issue_data.get("summary")
        or (issue_data.get("fields") or {}).get("summary", "")
        or ""
    )

    if issue_type != "test plan":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Issue {issue_key} is of type '{issue_type}'. "
                "Historical FAIL report only supports 'Test Plan' issue type."
            ),
        )

    fail_results = _get_all_fail_runs_historical(issue_key)
    kpm_count = sum(1 for r in fail_results if r["kpm_id"] != "No KPM")
    end_time = time.perf_counter()
    duration = int(round(end_time - start_time))

    return {
        "issue_key": issue_key,
        "issue_type": issue_type,
        "summary": summary,
        "mode": "historical",
        "note": "Includes tests that were rerun/reset after FAIL — not visible in current latestStatus.",
        "total_fail": len(fail_results),
        "with_kpm": kpm_count,
        "without_kpm": len(fail_results) - kpm_count,
        "results": fail_results,
        "execution_time_seconds": duration,
    }


# -- Tool: FAIL Overview (compact, UI-ready table) ----------------------------

_JIRA_BROWSE_URL = "https://skyway.porsche.com/jira/browse"
_KPM_TICKET_URL  = "https://kpmweb.vw.vwg/kpmweb/problemKlickOptimiert.xhtml?id="


@app.get(
    "/xray/fail-overview/{issue_key}",
    operation_id="xray_get_fail_overview",
    summary="Compact FAIL overview: test key, timestamp, tester, KPM link",
)
def xray_get_fail_overview(issue_key: str, historical: bool = False):
    """
    Return a compact, UI-ready overview of all FAILed tests in a Test Plan.

    Each row: test_key, test_url, summary, executed_on, tester_name,
    tester_email, test_exec_key, test_exec_url, kpm_id, kpm_url, comment.

    Use historical=true to include tests that were rerun/reset after FAIL.
    """
    start_time = time.perf_counter()

    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{issue_key}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found.")
        resp.raise_for_status()
        issue_data = resp.json()

    raw_issue_type = (
        issue_data.get("issuetype")
        or (issue_data.get("fields") or {}).get("issuetype")
        or issue_data.get("issueType")
        or issue_data.get("type")
        or ""
    )
    if isinstance(raw_issue_type, dict):
        raw_issue_type = raw_issue_type.get("name") or raw_issue_type.get("value") or ""
    issue_type = str(raw_issue_type).strip().lower()

    if issue_type != "test plan":
        raise HTTPException(
            status_code=400,
            detail=f"Issue {issue_key} is of type '{issue_type}'. Only 'Test Plan' is supported.",
        )

    plan_summary = (
        issue_data.get("summary")
        or (issue_data.get("fields") or {}).get("summary", "")
        or ""
    )

    fail_results = (
        _get_all_fail_runs_historical(issue_key)
        if historical
        else _get_fail_runs_for_test_plan(issue_key)
    )

    rows = []
    for r in fail_results:
        kpm_id   = r.get("kpm_id") or "No KPM"
        test_key = r.get("test_key") or ""
        exec_key = r.get("test_exec_key") or ""
        assignee = r.get("assignee") or {}
        rows.append({
            "test_key":      test_key,
            "test_url":      f"{_JIRA_BROWSE_URL}/{test_key}" if test_key else "",
            "summary":       r.get("summary") or "",
            "executed_on":   r.get("executed_on") or "",
            "tester_name":   assignee.get("displayName") or assignee.get("name") or "",
            "tester_email":  assignee.get("emailAddress") or "",
            "test_exec_key": exec_key,
            "test_exec_url": f"{_JIRA_BROWSE_URL}/{exec_key}" if exec_key else "",
            "kpm_id":        kpm_id,
            "kpm_url":       f"{_KPM_TICKET_URL}{kpm_id}" if kpm_id != "No KPM" else "",
            "comment":       r.get("comment") or "",
        })

    kpm_count = sum(1 for r in rows if r["kpm_id"] != "No KPM")
    end_time  = time.perf_counter()

    return {
        "issue_key":              issue_key,
        "summary":                plan_summary,
        "mode":                   "historical" if historical else "latest",
        "total_fail":             len(rows),
        "with_kpm":               kpm_count,
        "without_kpm":            len(rows) - kpm_count,
        "rows":                   rows,
        "execution_time_seconds": int(round(end_time - start_time)),
    }


# -- Helper: Generic status filter for a Test Plan ----------------------------

def _get_runs_by_status_for_test_plan(test_plan_key: str, status_filter: str) -> list[dict]:
    """
    Generic: collect all runs matching `status_filter` from a Test Plan.
    Reads latestStatus from /testplan/.../tests for initial key list, then
    paginates testruns to map keys → latest run_id, then builds results.
    `status_filter` must match xRay status label exactly (e.g. "BLOCKED", "FAIL").
    """
    # Step 1 — get test keys whose latestStatus matches the filter
    with get_local_client(timeout=60) as client:
        all_tests = _paginate_parallel(
            f"{XRAY_BASE_URL}/xray/testplan/{test_plan_key}/tests",
            {},
            client,
            stop_on_empty_only=True,  # xRay returns partial pages mid-pagination
        )

    target_keys: set[str] = set()
    for t in all_tests:
        latest = t.get("latestStatus") or t.get("status") or ""
        if isinstance(latest, dict):
            latest = latest.get("name") or latest.get("value") or ""
        if str(latest).upper() == status_filter.upper():
            key = t.get("key") or t.get("issueKey")
            if key:
                target_keys.add(key)

    if not target_keys:
        return []

    # Step 2 — fetch summaries AND paginate testruns in parallel (independent I/O)
    def _fetch_summaries_status() -> dict:
        return _fetch_issue_summaries(target_keys)

    def _fetch_testruns_status() -> dict:
        rmap: dict[str, dict] = {}
        with get_local_client(timeout=60) as client:
            all_runs = _paginate_parallel(
                f"{XRAY_BASE_URL}/xray/testruns",
                {"testPlanKey": test_plan_key},
                client,
                stop_on_empty_only=True,  # only stop on empty page
            )
        for run in all_runs:
            test_key = (
                run.get("testKey") or run.get("key") or run.get("issueKey")
                or (run.get("test") or {}).get("key")
            )
            run_status = run.get("status", "")
            if isinstance(run_status, dict):
                run_status = run_status.get("name") or run_status.get("value") or ""
            if test_key in target_keys and status_filter.upper() in str(run_status).upper():
                run_id = run.get("id")
                existing = rmap.get(test_key)
                if not existing or (run_id and run_id > existing.get("run_id", 0)):
                    rmap[test_key] = {
                        "run_id": run_id,
                        "test_exec_key": run.get("testExecKey") or run.get("testExecutionKey"),
                        "status": run_status,
                        "_run_detail": run,
                    }
        return rmap

    with ThreadPoolExecutor(max_workers=2) as outer:
        summary_fut = outer.submit(_fetch_summaries_status)
        testruns_fut = outer.submit(_fetch_testruns_status)
        issue_summaries = summary_fut.result()
        run_map = testruns_fut.result()

    return _build_results(run_map, issue_summaries)


# -- Tool: BLOCKED report (Test Plan only) -------------------------------------

@app.get(
    "/xray/blocked-report/{issue_key}",
    operation_id="xray_get_blocked_report",
    summary="Gets all BLOCKED test results with KPM IDs for a Test Plan",
)
def xray_get_blocked_report(issue_key: str):
    """
    Retrieve all BLOCKED test results with KPM IDs for a given Test Plan key.
    Only 'Test Plan' issue types are supported.
    """
    start_time = time.perf_counter()

    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{issue_key}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found.")
        resp.raise_for_status()
        issue_data = resp.json()

    raw_issue_type = (
        issue_data.get("issuetype")
        or (issue_data.get("fields") or {}).get("issuetype")
        or issue_data.get("issueType")
        or issue_data.get("type")
        or ""
    )
    if isinstance(raw_issue_type, dict):
        raw_issue_type = raw_issue_type.get("name") or raw_issue_type.get("value") or ""
    issue_type = str(raw_issue_type).strip().lower()

    summary = (
        issue_data.get("summary")
        or (issue_data.get("fields") or {}).get("summary", "")
        or ""
    )

    if issue_type != "test plan":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Issue {issue_key} is of type '{issue_type}'. "
                "Blocked report only supports 'Test Plan'."
            ),
        )

    blocked_results = _get_runs_by_status_for_test_plan(issue_key, "BLOCKED")
    # Enrich each blocked result with child issue/run information so callers
    # can see whether the BLOCKED entry is a test case or has child executions
    # (and which child execution is blocked and why).
    with get_local_client(timeout=30) as client:
        for r in blocked_results:
            try:
                test_key = (r.get("test_key") or "").strip()
                children: list[dict] = []

                if not test_key:
                    r["children"] = children
                    continue

                # Fetch the Jira/Xray issue for the test to discover subtasks / links
                resp = client.get(f"{XRAY_BASE_URL}/issue/{test_key}")
                if resp.status_code != 200:
                    r["children"] = children
                    continue

                issue_obj = resp.json()
                fields = issue_obj.get("fields") or {}

                # Collect explicit subtasks
                for sub in fields.get("subtasks", []) or []:
                    key = sub.get("key")
                    if key:
                        children.append({"key": key})

                # Collect issue links (both inward and outward)
                for link in fields.get("issuelinks", []) or []:
                    linked = link.get("outwardIssue") or link.get("inwardIssue")
                    if linked and linked.get("key"):
                        children.append({"key": linked.get("key")})

                # Deduplicate child keys
                seen = set()
                deduped = []
                for c in children:
                    k = c.get("key")
                    if not k or k in seen:
                        continue
                    seen.add(k)
                    deduped.append({"key": k})

                children = []
                # For each child, fetch its issue type and if it's a Test Execution
                # try to fetch the run details for this parent test to determine
                # status, comment and KPM.
                for c in deduped:
                    ck = c.get("key")
                    child_info = {"key": ck, "issue_type": None, "run_status": None, "kpm_id": None, "comment": None}
                    try:
                        cresp = client.get(f"{XRAY_BASE_URL}/issue/{ck}")
                        if cresp.status_code == 200:
                            cobj = cresp.json()
                            raw_it = (
                                cobj.get("issuetype")
                                or (cobj.get("fields") or {}).get("issuetype")
                                or cobj.get("issueType")
                                or cobj.get("type")
                                or ""
                            )
                            if isinstance(raw_it, dict):
                                raw_it = raw_it.get("name") or raw_it.get("value") or ""
                            child_info["issue_type"] = str(raw_it).strip()

                            # If child appears to be a Test Execution, try to fetch its testrun
                            if "execution" in child_info["issue_type"].lower() or "testexec" in ck.lower() or "testexec" in (cobj.get("key") or "").lower():
                                tr = client.get(
                                    f"{XRAY_BASE_URL}/xray/testrun",
                                    params={"testExecIssueKey": ck, "testIssueKey": test_key},
                                )
                                if tr.status_code == 200:
                                    tr_json = tr.json()
                                    # normalise status
                                    status = tr_json.get("status") or ""
                                    if isinstance(status, dict):
                                        status = status.get("name") or status.get("value") or ""
                                    child_info["run_status"] = str(status)
                                    # extract kpm/comment from the returned run object
                                    kpm = _get_kpm_from_run(tr_json) if tr_json else None
                                    child_info["kpm_id"] = kpm or "No KPM"
                                    raw_comment = tr_json.get("comment") if tr_json else ""
                                    if isinstance(raw_comment, dict):
                                        raw_comment = raw_comment.get("raw") or raw_comment.get("rendered") or ""
                                    child_info["comment"] = _normalize_text(raw_comment)

                    except Exception:
                        pass

                    children.append(child_info)

                r["children"] = children
            except Exception:
                r["children"] = []

    kpm_count = sum(1 for r in blocked_results if r["kpm_id"] != "No KPM")
    end_time = time.perf_counter()
    duration = int(round(end_time - start_time))

    return {
        "issue_key": issue_key,
        "issue_type": issue_type,
        "summary": summary,
        "total_blocked": len(blocked_results),
        "with_kpm": kpm_count,
        "without_kpm": len(blocked_results) - kpm_count,
        "results": blocked_results,
        "execution_time_seconds": duration,
    }


# -----------------------------
# Export helpers: XLSX + PDF
# -----------------------------
def _results_to_dataframe(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        assignee = r.get("assignee") or {}
        children = r.get("children") or []
        # children_keys: comma-separated list of child keys (flat values only)
        child_keys = ", ".join([str(c.get("key")) for c in children if c and c.get("key")])

        rows.append({
            "test_key": str(r.get("test_key") or ""),
            "summary": _normalize_text(r.get("summary") or ""),
            "test_exec_key": str(r.get("test_exec_key") or ""),
            "run_id": r.get("run_id") or "",
            "status": str(r.get("status") or ""),
            "kpm_id": str(r.get("kpm_id") or ""),
            "comment": _normalize_text(r.get("comment") or ""),
            "assignee_name": (assignee.get("displayName") or assignee.get("name") or ""),
            "assignee_email": (assignee.get("emailAddress") or ""),
            "children_keys": child_keys,
        })
    df = pd.DataFrame(rows)
    # Ensure stable column order
    cols = [
        "test_key", "summary", "test_exec_key", "run_id", "status",
        "kpm_id", "comment", "assignee_name", "assignee_email", "children_keys",
    ]
    return df[[c for c in cols if c in df.columns]]


def _build_html_report(title: str, df: pd.DataFrame) -> str:
    style = '''
    <style>
      body { font-family: Arial, Helvetica, sans-serif; font-size:12px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 6px; }
      th { background: #f4f4f4; text-align: left; }
      tr:nth-child(even) { background: #fbfbfb; }
      .nowrap { white-space: nowrap; }
      .small { font-size: 10px; color: #444; }
    </style>
    '''
    html = ["<html><head>", style, f"<title>{_html.escape(title)}</title>", "</head><body>"]
    html.append(f"<h2>{_html.escape(title)}</h2>")
    html.append(df.to_html(index=False, classes='table', escape=False))
    html.append("</body></html>")
    return "\n".join(html)


@app.get("/export/fail/{issue_key}.xlsx", summary="Export FAIL report as XLSX")
def export_fail_xlsx(issue_key: str):
    # Reuse the historical fail pipeline to validate the issue and collect results
    report = xray_get_fail_report_historical(issue_key)
    results = report.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="No FAIL results to export.")

    df = _results_to_dataframe(results)

    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Fails', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Fails']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # set column width to max of header or data
            col_data = df[value].astype(str).fillna('')
            max_len = max(col_data.map(len).max() if len(col_data) else 0, len(value))
            worksheet.set_column(col_num, col_num, min(max_len + 4, 60))
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        worksheet.freeze_panes(1, 0)
    bio.seek(0)
    filename = f"{issue_key}_Fails.xlsx"
    return StreamingResponse(bio, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={
        'Content-Disposition': f'attachment; filename="{filename}"'
    })


@app.get("/export/blocked/{issue_key}.xlsx", summary="Export BLOCKED report as XLSX")
def export_blocked_xlsx(issue_key: str):
    report = xray_get_blocked_report(issue_key)
    results = report.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="No BLOCKED results to export.")

    df = _results_to_dataframe(results)

    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Blocked', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Blocked']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#FFF3CD'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            col_data = df[value].astype(str).fillna('')
            max_len = max(col_data.map(len).max() if len(col_data) else 0, len(value))
            worksheet.set_column(col_num, col_num, min(max_len + 4, 60))
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        worksheet.freeze_panes(1, 0)
    bio.seek(0)
    filename = f"{issue_key}_Blocked.xlsx"
    return StreamingResponse(bio, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={
        'Content-Disposition': f'attachment; filename="{filename}"'
    })


@app.get("/export/fail/{issue_key}.pdf", summary="Export FAIL report as PDF (HTML→PDF)")
def export_fail_pdf(issue_key: str):
    report = xray_get_fail_report_historical(issue_key)
    results = report.get('results', [])
    if not results:
        raise HTTPException(status_code=404, detail='No FAIL results to export.')

    df = _results_to_dataframe(results)
    html = _build_html_report(f"{issue_key} - FAIL Report", df)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise HTTPException(status_code=501, detail='Playwright not installed. Install with `pip install playwright` and run `playwright install`.')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until='networkidle')
        pdf_bytes = page.pdf(format='A4', print_background=True)
        browser.close()

    bio = io.BytesIO(pdf_bytes)
    bio.seek(0)
    filename = f"{issue_key}_Fails.pdf"
    return StreamingResponse(bio, media_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="{filename}"'
    })


@app.get("/export/blocked/{issue_key}.pdf", summary="Export BLOCKED report as PDF (HTML→PDF)")
def export_blocked_pdf(issue_key: str):
    report = xray_get_blocked_report(issue_key)
    results = report.get('results', [])
    if not results:
        raise HTTPException(status_code=404, detail='No BLOCKED results to export.')

    df = _results_to_dataframe(results)
    html = _build_html_report(f"{issue_key} - BLOCKED Report", df)

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        raise HTTPException(status_code=501, detail='Playwright not installed. Install with `pip install playwright` and run `playwright install`.')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until='networkidle')
        pdf_bytes = page.pdf(format='A4', print_background=True)
        browser.close()

    bio = io.BytesIO(pdf_bytes)
    bio.seek(0)
    filename = f"{issue_key}_Blocked.pdf"
    return StreamingResponse(bio, media_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="{filename}"'
    })


@app.get(
    "/mail/trigger/{issue_key}",
    operation_id="mail_trigger_preview",
    summary="Preview mail recipients from historical FAIL results without KPM",
)
def mail_trigger_preview(issue_key: str):
    """
    Build a mail preview list from historical FAIL results.

    Only rows without a KPM ID are considered mail candidates.
    Returns a compact payload for UI rendering and dry-run email triggers.
    """
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{issue_key}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found.")
        resp.raise_for_status()
        issue_data = resp.json()

    raw_issue_type = (
        issue_data.get("issuetype")
        or (issue_data.get("fields") or {}).get("issuetype")
        or issue_data.get("issueType")
        or issue_data.get("type")
        or ""
    )
    if isinstance(raw_issue_type, dict):
        raw_issue_type = raw_issue_type.get("name") or raw_issue_type.get("value") or ""
    issue_type = str(raw_issue_type).strip().lower()
    if issue_type != "test plan":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Issue {issue_key} is of type '{issue_type}'. "
                "Mail trigger preview only supports 'Test Plan'."
            ),
        )

    summary = (
        issue_data.get("summary")
        or (issue_data.get("fields") or {}).get("summary", "")
        or ""
    )

    historical_results = _get_all_fail_runs_historical(issue_key)

    rows = []
    candidates = []
    for item in historical_results:
        kpm_id = str(item.get("kpm_id") or "No KPM").strip()
        assignee = item.get("assignee") or {}
        display_name = (assignee.get("displayName") or assignee.get("name") or "").strip()
        email = (assignee.get("emailAddress") or "").strip()

        row = {
            "test_key": item.get("test_key") or "",
            "kpm_id": kpm_id,
            "display_name": display_name,
            "email": email,
            "can_email": bool(email),
            "no_kpm": (kpm_id == "No KPM"),
        }
        rows.append(row)

        if kpm_id != "No KPM":
            continue

        candidates.append(row)

    rows.sort(key=lambda x: x.get("test_key") or "")
    candidates.sort(key=lambda x: x.get("test_key") or "")

    return {
        "issue_key": issue_key,
        "issue_type": issue_type,
        "summary": summary,
        "source": "historical",
        "total_historical_fail": len(historical_results),
        "rows": rows,
        "no_kpm_count": len(candidates),
        "emailable_no_kpm_count": sum(1 for c in candidates if c["can_email"]),
        "candidates": candidates,
        "mail_template": {
            "subject": "[Action Needed] Failed test without KPM - {test_key}",
            "body": "Please create a KPM ticket for failed test {test_key}."
        },
    }


_SMTP_HOST = os.getenv("SMTP_HOST", "appmail.emea.porsche.biz")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
_SMTP_FROM = os.getenv("SMTP_FROM", "failed-noKPM-dev@porsche-engineering.de")


def _build_mail_html(test_key: str, display_name: str, issue_key: str, summary: str) -> str:
    jira_url = f"https://skyway.porsche.com/jira/browse/{test_key}"
    plan_url = f"https://skyway.porsche.com/jira/browse/{issue_key}"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:600px;margin:0 auto;">
  <div style="background:#1a1a2e;padding:18px 24px;border-radius:8px 8px 0 0;">
    <h2 style="color:#fff;margin:0;font-size:1.1rem;">&#9888; Action Required: Failed Test Without KPM</h2>
  </div>
  <div style="border:1px solid #ddd;border-top:none;padding:24px;border-radius:0 0 8px 8px;">
    <p>Hi {display_name or 'Team'},</p>
    <p>The following test has been marked as <strong>FAIL</strong> but has <strong>no KPM ticket</strong> linked to it:</p>
    <table style="border-collapse:collapse;width:100%;margin:16px 0;">
      <tr style="background:#f4f4f4;">
        <td style="padding:8px 12px;font-weight:600;width:140px;">Test Key</td>
        <td style="padding:8px 12px;"><a href="{jira_url}" style="color:#0052cc;">{test_key}</a></td>
      </tr>
      <tr>
        <td style="padding:8px 12px;font-weight:600;">Test Plan</td>
        <td style="padding:8px 12px;"><a href="{plan_url}" style="color:#0052cc;">{issue_key}</a>{(' — ' + summary) if summary else ''}</td>
      </tr>
    </table>
    <p><strong>Please create a KPM ticket</strong> for this failure and link it in the test run comment using the format:</p>
    <pre style="background:#f8f8f8;padding:10px 14px;border-left:4px solid #e00;font-size:13px;">KPM: &lt;kpm-id&gt;</pre>
    <p style="color:#555;font-size:12px;margin-top:24px;">
      This notification was generated automatically by the MLB TestPlan MCP server.<br>
      Do not reply to this email.
    </p>
  </div>
</body>
</html>"""


@app.post(
    "/mail/trigger/{issue_key}/send",
    operation_id="mail_trigger_send_dry_run",
    summary="Send (or dry-run) mail to assignees of historical FAIL results without KPM",
)
def mail_trigger_send_dry_run(
    issue_key: str,
    test_keys: list[str] = Body(default=[]),
    dry_run: bool = Body(default=False),
):
    """
    Send emails to assignees of failed tests that have no KPM.

    - dry_run=false (default): sends real emails via SMTP
    - dry_run=true: returns recipients/payload without sending

    If test_keys are provided, only those candidates are emailed;
    otherwise all emailable no-KPM candidates are selected.
    """
    import smtplib
    from email.message import EmailMessage

    preview = mail_trigger_preview(issue_key)
    plan_summary = preview.get("summary", "")
    selected_keys = {k.strip().upper() for k in (test_keys or []) if str(k).strip()}

    selected = []
    for c in preview["candidates"]:
        if not c.get("can_email"):
            continue
        if selected_keys and (c.get("test_key") or "").upper() not in selected_keys:
            continue
        selected.append(c)

    recipient_list = [
        {"test_key": r["test_key"], "display_name": r["display_name"], "email": r["email"]}
        for r in selected
    ]

    if dry_run:
        return {
            "issue_key": issue_key,
            "smtp_enabled": True,
            "mode": "dry_run",
            "selected_count": len(selected),
            "selected_recipients": recipient_list,
            "smtp_host": _SMTP_HOST,
            "smtp_port": _SMTP_PORT,
            "smtp_from": _SMTP_FROM,
            "message": "Dry run — no emails sent.",
        }

    sent = []
    failed = []

    for r in selected:
        try:
            msg = EmailMessage()
            msg["From"] = _SMTP_FROM
            msg["To"] = r["email"]
            msg["Subject"] = f"[Action Needed] Failed test without KPM — {r['test_key']}"
            html_body = _build_mail_html(r["test_key"], r["display_name"], issue_key, plan_summary)
            msg.set_content(
                f"Hi {r['display_name'] or 'Team'},\n\n"
                f"Test {r['test_key']} is marked FAIL with no KPM linked.\n"
                f"Please create a KPM ticket and add it to the test run comment.\n\n"
                f"Test Plan: {issue_key}\nJira: https://skyway.porsche.com/jira/browse/{r['test_key']}"
            )
            msg.add_alternative(html_body, subtype="html")

            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=30) as smtp:
                smtp.send_message(msg)

            sent.append({"test_key": r["test_key"], "email": r["email"]})
        except Exception as e:
            failed.append({"test_key": r["test_key"], "email": r["email"], "error": str(e)})

    return {
        "issue_key": issue_key,
        "smtp_enabled": True,
        "mode": "live",
        "selected_count": len(selected),
        "sent_count": len(sent),
        "failed_count": len(failed),
        "sent": sent,
        "failed": failed,
        "smtp_host": _SMTP_HOST,
        "smtp_from": _SMTP_FROM,
    }
# =============================================================================
# ROLLOVER: Clone a Confluence Test Plan page + all linked Jira Test Plans
# =============================================================================

import base64 as _b64


def _jira_auth_headers() -> dict:
    """Return auth + JSON content headers.

    Supports two auth modes:
    - PAT only (Jira Server/DC): set JIRA_API_TOKEN, leave JIRA_EMAIL empty
      → sends Bearer <token>
    - Basic auth (Jira Cloud): set both JIRA_EMAIL + JIRA_API_TOKEN
      → sends Basic base64(email:token)
    """
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "") or os.getenv("JIRA_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=500,
            detail="JIRA_API_TOKEN not configured in .env",
        )
    if email:
        # Basic auth (Jira Cloud)
        creds = _b64.b64encode(f"{email}:{token}".encode()).decode()
        auth_value = f"Basic {creds}"
    else:
        # Bearer PAT (Jira Server / Data Center)
        auth_value = f"Bearer {token}"
    return {
        "Authorization": auth_value,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _extract_jira_keys_from_xhtml(xhtml: str, project_key_pattern: str = r"[A-Z][A-Z0-9]+") -> list:
    """
    Return all unique Jira issue keys found in Confluence storage XHTML.
    Matches keys in macro parameters, JQL text, URLs, and plain text.
    Order is preserved (first occurrence wins for deduplication).
    """
    pattern = re.compile(rf"\b({project_key_pattern}-\d+)\b")
    seen: set = set()
    result: list = []
    for k in pattern.findall(xhtml):
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def _substitute_keys_in_xhtml(xhtml: str, key_map: dict) -> str:
    """
    Replace every occurrence of each old Jira key with its new key throughout
    the raw XHTML body — covers macro parameters, JQL queries, link URLs, and
    plain text.  Longer keys are replaced first to prevent partial matches
    (e.g. OTA-1 matching inside OTA-10).
    """
    for old_key in sorted(key_map.keys(), key=len, reverse=True):
        xhtml = re.sub(rf"\b{re.escape(old_key)}\b", key_map[old_key], xhtml)
    return xhtml


def _get_confluence_page_with_storage(page_id: str) -> dict:
    """
    Fetch a Confluence page (storage body + metadata) via the local proxy at
    LOCAL_API_URL (port 8001) — the same proxy used by every other endpoint in
    this server.  No external credentials are required.
    """
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{LOCAL_API_URL}/page/{page_id}")
        if resp.status_code in (301, 302):
            resp = client.get(resp.headers.get("location", ""))
        resp.raise_for_status()
        data = resp.json()

    confluence_base = os.getenv("CONFLUENCE_BASE_URL", "https://api.skyway.porsche.com/confluence")
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "space_key": data.get("space"),
        "version_number": data.get("version") or 1,
        "parent_id": None,   # local proxy does not expose ancestors; populated below if needed
        "xhtml_body": data.get("body", ""),
        "url": data.get("url") or f"{confluence_base}/pages/viewpage.action?pageId={page_id}",
    }


def _clone_jira_issue(source_key: str, field_overrides: dict, headers: dict) -> dict:
    """
    Clone a Jira issue, replicating a manual Jira clone exactly:
    1. Read ALL fields from source (including custom fields like Teams, Markets)
    2. Create new issue via proxy /create_issue (standard fields)
    3. PUT all custom fields to the new issue via Jira REST API directly
    4. Copy Xray test associations if this is a Test Plan
    """
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/issue/{source_key}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Source issue {source_key} not found")
        resp.raise_for_status()
        issue_data = resp.json()

    # The proxy may return fields nested under "fields" or at top level
    raw = issue_data.get("fields") or issue_data

    project_key = (raw.get("project") or {}).get("key") or issue_data.get("project")
    if isinstance(project_key, dict):
        project_key = project_key.get("key")

    issuetype = (raw.get("issuetype") or {}).get("name") or issue_data.get("issuetype")
    if isinstance(issuetype, dict):
        issuetype = issuetype.get("name")

    summary = f"CLONE - {raw.get('summary') or issue_data.get('summary') or source_key}"
    description = raw.get("description") or issue_data.get("description") or ""

    labels = raw.get("labels") or issue_data.get("labels") or []
    components_raw = raw.get("components") or issue_data.get("components") or []
    components = [c.get("name") if isinstance(c, dict) else c for c in components_raw]

    fix_versions_raw = raw.get("fixVersions") or issue_data.get("fixVersions") or []
    fix_versions = [v.get("name") if isinstance(v, dict) else v for v in fix_versions_raw]

    # Apply caller overrides
    if field_overrides.get("summary"):
        summary = field_overrides["summary"]
    if field_overrides.get("fixVersions"):
        fv = field_overrides["fixVersions"]
        fix_versions = [v.get("name") if isinstance(v, dict) else v for v in fv]

    params: dict = {
        "project_key": project_key,
        "summary": summary,
        "description": description or "",
        "issuetype": issuetype or "Test Plan",
    }
    # Assignee intentionally skipped — display names are not valid Jira usernames
    if labels:
        params["labels"] = labels
    if components:
        params["components"] = components
    if fix_versions:
        params["fix_versions"] = fix_versions

    with get_local_client(timeout=30) as client:
        resp = client.post(f"{XRAY_BASE_URL}/create_issue", params=params)
        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to clone {source_key}: {resp.text[:500]}",
            )
        created = resp.json()

    new_key = created.get("key")

    # --- Step 2: Copy ALL custom fields (Teams, Markets, etc.) via direct Jira REST ---
    if new_key:
        custom_fields_update: dict = {}
        for field_id, value in raw.items():
            if field_id.startswith("customfield_") and value is not None:
                custom_fields_update[field_id] = value
        # Apply explicit customfield_ overrides from caller
        for k, v in field_overrides.items():
            if k.startswith("customfield_"):
                custom_fields_update[k] = v

        if custom_fields_update:
            jira_base = os.getenv("JIRA_BASE_URL", "https://skyway.porsche.com/jira")
            auth_headers = _jira_auth_headers()
            try:
                with get_client(timeout=30) as client:
                    client.put(
                        f"{jira_base}/rest/api/2/issue/{new_key}",
                        headers={**auth_headers, "Content-Type": "application/json"},
                        json={"fields": custom_fields_update},
                    )
                created["_custom_fields_copied"] = list(custom_fields_update.keys())
            except Exception as exc:
                created["_custom_fields_copied"] = f"error: {exc}"

    # --- Step 3: Copy Xray test associations (Test Plan only) ---
    if new_key and (issuetype or "").lower() == "test plan":
        try:
            all_test_keys: list[str] = []
            page = 1
            while True:
                with get_local_client(timeout=30) as client:
                    r = client.get(
                        f"{XRAY_BASE_URL}/xray/testplan/{source_key}/tests",
                        params={"page": page, "limit": 100},
                    )
                if r.status_code != 200:
                    break
                batch = r.json()
                if not batch:
                    break
                if isinstance(batch, dict):
                    batch = batch.get("tests") or batch.get("results") or []
                test_keys = [
                    t.get("key") or t.get("issueKey")
                    for t in batch
                    if isinstance(t, dict) and (t.get("key") or t.get("issueKey"))
                ]
                all_test_keys.extend(test_keys)
                if len(batch) < 100:
                    break
                page += 1

            if all_test_keys:
                add_errors = []
                jira_base = os.getenv("JIRA_BASE_URL", "https://skyway.porsche.com/jira")
                auth_headers = _jira_auth_headers()
                for i in range(0, len(all_test_keys), 50):
                    chunk = all_test_keys[i:i + 50]
                    with get_client(timeout=60) as client:
                        add_resp = client.post(
                            f"{jira_base}/rest/raven/1.0/api/testplan/{new_key}/test",
                            headers={**auth_headers, "Content-Type": "application/json"},
                            json={"add": chunk},
                        )
                        if add_resp.status_code not in (200, 201, 204):
                            add_errors.append(f"chunk {i}-{i+len(chunk)}: HTTP {add_resp.status_code} — {add_resp.text[:300]}")
                created["_xray_tests_copied"] = len(all_test_keys)
                if add_errors:
                    created["_xray_add_errors"] = add_errors
            else:
                created["_xray_tests_copied"] = 0
        except Exception:
            created["_xray_tests_copied"] = "error — check manually"

    return created


def _create_confluence_page(space_key: str, parent_id: Optional[str],
                             title: str, xhtml_body: str) -> dict:
    """
    Create a new Confluence page with the given storage XHTML body.
    Returns {id, title, url} of the created page.
    """
    confluence_base = os.getenv("CONFLUENCE_BASE_URL", "https://api.skyway.porsche.com/confluence")
    headers = _jira_auth_headers()

    payload: dict = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": xhtml_body,
                "representation": "storage",
            }
        },
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]

    with get_client(timeout=60) as client:
        resp = client.post(
            f"{confluence_base}/rest/api/content",
            headers=headers,
            json=payload,
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to create Confluence page: {resp.text[:500]}",
            )
        data = resp.json()

    links = data.get("_links") or {}
    base_url = links.get("base", confluence_base)
    web_ui = links.get("webui", "")
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "url": f"{base_url}{web_ui}" if web_ui else "",
    }


@app.post(
    "/rollover/clone",
    operation_id="rollover_clone_test_plan_page",
    summary="Clone a Confluence Test Plan page and all linked Jira Test Plans (rollover)",
)
def rollover_clone_test_plan_page(
    source_page_id: str = Body(..., description="Confluence page ID of the source Test Plan page (e.g. '2558891351')"),
    new_page_title: str = Body(..., description="Title for the cloned Confluence page"),
    dry_run: bool = Body(default=True, description="When true (default), shows the key mapping and XHTML preview WITHOUT creating anything in Jira or Confluence"),
    field_overrides: dict = Body(default={}, description="Optional Jira field overrides applied to every cloned issue, e.g. {\"fixVersions\": [{\"name\": \"SOP2\"}]}"),
    jira_key_pattern: str = Body(default=r"[A-Z][A-Z0-9]+", description="Regex fragment that matches the project key prefix. Default matches any project (OTA, MLBEVO, etc.)."),
):
    """
    Full Test Plan rollover workflow executed in one call:

    1. Read the source Confluence page (XHTML storage body + metadata).
    2. Extract every Jira issue key referenced anywhere in the page.
    3. For each key: clone the Jira issue (skipped when dry_run=True).
    4. Build an old→new key mapping table.
    5. Substitute every occurrence of old keys with new keys throughout the
       XHTML (macro parameters, JQL queries, link URLs, plain text).
    6. Create a new Confluence page with the updated XHTML (skipped when dry_run=True).
    7. Return a full report: key mapping, new page URL, and any per-key failures.

    Safe by default — dry_run=True will never write to Jira or Confluence.
    Individual clone failures do NOT abort the whole process; they are collected
    and reported in the `failures` field so you can take manual action.
    """
    start_time = time.perf_counter()
    failures: list = []

    # ------------------------------------------------------------------
    # Step 1: Read source Confluence page
    # ------------------------------------------------------------------
    try:
        page = _get_confluence_page_with_storage(source_page_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read source Confluence page {source_page_id}: {exc}",
        )

    xhtml_body = page["xhtml_body"]
    if not xhtml_body:
        raise HTTPException(
            status_code=422,
            detail=f"Source page {source_page_id} returned an empty storage body.",
        )

    # ------------------------------------------------------------------
    # Step 2: Extract Jira keys
    # ------------------------------------------------------------------
    all_keys = _extract_jira_keys_from_xhtml(xhtml_body, project_key_pattern=jira_key_pattern)
    if not all_keys:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No Jira issue keys matching pattern '{jira_key_pattern}-\\d+' "
                f"were found in page {source_page_id}."
            ),
        )

    # ------------------------------------------------------------------
    # Step 3: Clone each Jira issue (or build dry-run placeholders)
    # ------------------------------------------------------------------
    key_map: dict = {}
    cloned_issues: list = []

    if dry_run:
        # Dry run: produce placeholder new keys for preview only
        for i, old_key in enumerate(all_keys, start=1):
            placeholder = f"NEW-{i:04d}"
            key_map[old_key] = placeholder
            cloned_issues.append({
                "old_key": old_key,
                "new_key": placeholder,
                "dry_run": True,
                "note": "Not created — dry_run=True",
            })
    else:
        try:
            auth_headers = _jira_auth_headers()
        except HTTPException:
            raise

        for old_key in all_keys:
            try:
                new_issue = _clone_jira_issue(old_key, field_overrides, auth_headers)
                new_key = new_issue.get("key")
                if not new_key:
                    raise ValueError(f"Clone returned no key: {new_issue}")
                key_map[old_key] = new_key
                cloned_issues.append({
                    "old_key": old_key,
                    "new_key": new_key,
                    "new_issue_id": new_issue.get("id"),
                })
            except Exception as exc:
                failures.append({"old_key": old_key, "step": "clone_jira_issue", "error": str(exc)})
                # Continue — partial rollover is acceptable

    # ------------------------------------------------------------------
    # Step 4 + 5: Substitute keys in XHTML
    # ------------------------------------------------------------------
    updated_xhtml = _substitute_keys_in_xhtml(xhtml_body, key_map)

    # ------------------------------------------------------------------
    # Step 6: Create the cloned Confluence page
    # ------------------------------------------------------------------
    new_page_info: Optional[dict] = None

    if not dry_run:
        if not key_map:
            failures.append({
                "step": "create_confluence_page",
                "error": "Skipped — no keys were successfully cloned.",
            })
        else:
            try:
                new_page_info = _create_confluence_page(
                    space_key=page["space_key"],
                    parent_id=page["parent_id"],
                    title=new_page_title,
                    xhtml_body=updated_xhtml,
                )
            except Exception as exc:
                failures.append({"step": "create_confluence_page", "error": str(exc)})

    end_time = time.perf_counter()

    return {
        "source_page_id": source_page_id,
        "source_page_title": page["title"],
        "source_page_url": page["url"],
        "new_page_title": new_page_title,
        "dry_run": dry_run,
        "keys_found": len(all_keys),
        "keys_found_list": all_keys,
        "keys_cloned": len(key_map),
        "key_mapping": key_map,
        "cloned_issues": cloned_issues,
        "new_confluence_page": new_page_info,
        "failures": failures,
        "failure_count": len(failures),
        # Include first 3000 chars of updated XHTML in dry-run so caller can
        # inspect that key substitution looks correct before committing.
        "xhtml_preview": updated_xhtml[:3000] if dry_run else None,
        "execution_time_seconds": round(end_time - start_time, 2),
    }


# =============================================================================
# ROLLOVER: Clone a single Jira issue and return the new ID
# =============================================================================

@app.post(
    "/rollover/clone-issue",
    operation_id="rollover_clone_single_issue",
    summary="Clone a single Jira issue and return the new ID (sandbox-safe)",
)
def rollover_clone_single_issue(
    source_key: str = Body(..., description="Jira issue key to clone, e.g. 'OTA-6264'"),
    dry_run: bool = Body(default=True, description="When true: reads the issue and shows what would be cloned, without creating anything"),
    field_overrides: dict = Body(default={}, description="Optional field overrides, e.g. {\"summary\": \"My clone\"}"),
):
    """
    Clone a single Jira issue and return the newly created issue key.

    - dry_run=true  → reads the source issue fields and returns a preview (no write)
    - dry_run=false → creates a real clone in Jira and returns the new key/id
    """
    jira_base = os.getenv("JIRA_BASE_URL", "https://api.skyway.porsche.com/jira")

    # Always read the source issue (works without credentials via proxy on port 8000)
    try:
        with get_local_client(timeout=30) as client:
            resp = client.get(f"{XRAY_BASE_URL}/issue/{source_key}")
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Issue {source_key} not found")
            resp.raise_for_status()
            issue_data = resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read {source_key}: {exc}")

    # Build a summary of what would be cloned
    fields_preview = {
        "summary": f"CLONE - {issue_data.get('summary', source_key)}",
        "issuetype": issue_data.get("issuetype"),
        "project": issue_data.get("project"),
        "priority": issue_data.get("priority"),
        "labels": issue_data.get("labels"),
        "components": issue_data.get("components"),
        "fixVersions": issue_data.get("fixVersions"),
        "assignee": issue_data.get("assignee"),
    }
    if field_overrides:
        fields_preview.update(field_overrides)

    if dry_run:
        return {
            "source_key": source_key,
            "dry_run": True,
            "note": "No issue created — dry_run=True",
            "would_clone_fields": {k: v for k, v in fields_preview.items() if v is not None},
        }

    # --- Live clone: delegate to _clone_jira_issue (handles custom fields + Xray tests) ---
    try:
        created = _clone_jira_issue(source_key, field_overrides, {})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Clone failed: {exc}")

    new_key = created.get("key")
    new_id = created.get("id")
    jira_ui_url = f"{jira_base}/browse/{new_key}" if new_key else None
    issuetype_name = (created.get("fields") or {}).get("issuetype", {}).get("name") or "Test Plan"
    project_key = (created.get("fields") or {}).get("project", {}).get("key") or source_key.split("-")[0]
    summary = created.get("fields", {}).get("summary") or f"CLONE - {source_key}"

    return {
        "source_key": source_key,
        "dry_run": False,
        "new_key": new_key,
        "new_id": new_id,
        "jira_url": jira_ui_url,
        "xray_tests_copied": created.get("_xray_tests_copied"),
        "xray_add_errors": created.get("_xray_add_errors"),
        "custom_fields_copied": created.get("_custom_fields_copied"),
        "cloned_fields_summary": {
            "summary": f"CLONE - {source_key}",
            "issuetype": "Test Plan",
            "project": source_key.split("-")[0],
        },
    }


# =============================================================================
# TEMPORARY: JQL-based FAIL + KPM scan across Test Executions
# =============================================================================

@app.get(
    "/tmp/jql-fail-report",
    operation_id="tmp_jql_fail_report",
    summary="[TEMP] Run JQL, collect all matched Test Executions, return FAIL+KPM results",
)
def tmp_jql_fail_report(
    jql: str,
    max_executions: int = 200,
    offset: int = 0,
):
    """
    Temporary endpoint — same output shape as xray_get_fail_report.

    Use offset + max_executions to scan in chunks:
      offset=0,   max_executions=100  → executions 1–100
      offset=100, max_executions=100  → executions 101–200
      offset=200, max_executions=100  → executions 201–300
      ...

    Steps:
      1. Run JQL via proxy /search_issues — expects Test Execution issues
      2. For every matched Test Execution key, paginate /xray/testruns?testExecKey=
         and collect FAIL runs (same logic as existing helpers)
      3. Fetch KPM from each FAIL run comment (reuses _get_kpm_from_run)
      4. Fetch test summaries in parallel (reuses _fetch_issue_summary)
      5. Return same shape as xray_get_fail_report
    """
    import time as _time
    import traceback as _tb
    start = _time.perf_counter()

    # --- Step 1: Run JQL, collect Test Execution keys ---
    # The proxy /search_issues does NOT support pagination — it always returns
    # the same page. Fetch all needed keys in a single call with max_results=max_executions.
    exec_keys: list[str] = []
    with get_local_client(timeout=60) as client:
        resp = client.get(
            f"{XRAY_BASE_URL}/search_issues",
            params={"jql": jql, "max_results": max_executions},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"JQL search failed: {resp.text[:300]}")
    data = resp.json()
    issues = data if isinstance(data, list) else data.get("issues", [])
    seen_keys: set[str] = set()
    for iss in issues:
        key = iss.get("key") or iss.get("issueKey")
        if key and key not in seen_keys:
            seen_keys.add(key)
            exec_keys.append(key)
    # Apply offset slice BEFORE capping at max_executions
    exec_keys = exec_keys[offset:offset + max_executions]

    # --- Step 2: Fetch FAIL runs from all executions IN PARALLEL ---
    from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed

    def _scan_execution(exec_key: str) -> list[dict]:
        """Return list of FAIL run dicts for one Test Execution."""
        fail_runs = []
        for page in range(1, 50):
            try:
                with get_local_client(timeout=30) as client:
                    r = client.get(
                        f"{XRAY_BASE_URL}/xray/testruns",
                        params={"testExecKey": exec_key, "page": page, "limit": 100},
                    )
            except Exception:
                break
            if r.status_code != 200:
                break
            runs = _extract_items(r.json())
            if not runs:
                break
            for run in runs:
                status = run.get("status", "")
                if isinstance(status, dict):
                    status = status.get("name") or status.get("value") or ""
                if "FAIL" not in str(status).upper():
                    continue
                test_key = (
                    run.get("testKey") or run.get("key") or run.get("issueKey")
                    or (run.get("test") or {}).get("key")
                )
                if not test_key:
                    continue
                fail_runs.append({
                    "test_key": test_key,
                    "run_id": run.get("id"),
                    "test_exec_key": exec_key,
                })
            if len(runs) < 100:
                break
        return fail_runs

    # Collect ALL fail runs (no deduplication) — keyed by run_id to avoid true dups
    run_map: dict[int, dict] = {}  # run_id -> {test_key, run_id, test_exec_key, status}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_scan_execution, k): k for k in exec_keys}
        for fut in _as_completed(futures):
            for run in fut.result():
                run_id = run["run_id"]
                if run_id and run_id not in run_map:
                    run_map[run_id] = {
                        "test_key": run["test_key"],
                        "run_id": run_id,
                        "test_exec_key": run["test_exec_key"],
                        "status": "FAIL",
                    }

    if not run_map:
        return {
            "jql": jql,
            "executions_scanned": len(exec_keys),
            "executions_list": exec_keys,
            "total_fail": 0,

            "with_kpm": 0,
            "without_kpm": 0,
            "results": [],
            "execution_time_seconds": round(_time.perf_counter() - start, 2),
        }

    # --- Step 3: Fetch run details + KPM in parallel ---
    def _fetch_run_and_kpm(run_id: int, info: dict):
        test_exec_key = info.get("test_exec_key")
        test_key = info.get("test_key")
        kpm_id = "No KPM"
        comment = ""
        if run_id:
            try:
                with get_local_client(timeout=20) as client:
                    r = client.get(f"{XRAY_BASE_URL}/xray/testrun/{run_id}")
                if r.status_code == 200:
                    run_detail = r.json()
                    kpm_id = _get_kpm_from_run(run_detail) or "No KPM"
                    raw_comment = run_detail.get("comment") or ""
                    comment = _normalize_text(raw_comment)
            except Exception:
                pass
        return run_id, test_key, kpm_id, comment, test_exec_key

    kpm_map: dict[int, tuple] = {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_fetch_run_and_kpm, rid, v): rid for rid, v in run_map.items()}
        for fut in _as_completed(futures):
            rid, tk, kpm, cmt, exec_key = fut.result()
            kpm_map[rid] = (tk, kpm, cmt, exec_key)

    # --- Step 4: Fetch test summaries in parallel ---
    unique_test_keys = {v["test_key"] for v in run_map.values()}
    summaries: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_fetch_issue_summary, k): k for k in unique_test_keys}
        for fut in _as_completed(futures):
            k = futures[fut]
            try:
                summaries[k] = fut.result()
            except Exception:
                summaries[k] = ""

    # --- Step 5: Build results ---
    results = []
    for rid, (test_key, kpm, cmt, exec_key) in kpm_map.items():
        results.append({
            "test_key": test_key,
            "test_summary": summaries.get(test_key, ""),
            "test_exec_key": exec_key,
            "run_id": rid,
            "status": "FAIL",
            "kpm_id": kpm,
            "comment": cmt,
        })

    results.sort(key=lambda x: (x["test_exec_key"], x["test_key"]))
    kpm_count = sum(1 for r in results if r["kpm_id"] != "No KPM")

    return {
        "jql": jql,
        "executions_scanned": len(exec_keys),
        "executions_list": exec_keys,
        "total_fail": len(results),
        "with_kpm": kpm_count,
        "without_kpm": len(results) - kpm_count,
        "results": results,
        "execution_time_seconds": round(_time.perf_counter() - start, 2),
    }


# -- Mount MCP + run -----------------------------------------------------------
# NEW
mcp = FastApiMCP(app)
mcp.mount(mount_path="/mcp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)