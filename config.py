import os
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://api.skyway.porsche.com/jira")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL", "https://api.skyway.porsche.com/confluence")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "2378907792")

XRAY_BASE_URL = os.getenv("XRAY_BASE_URL", "http://localhost:8000")
LOCAL_API_URL = os.getenv("LOCAL_API_URL", "http://localhost:8001")

# Alias map from your spec
ALIASES = {
    "europe": "Testing ECE", "ece": "Testing ECE",
    "north america": "Testing NAR", "nar": "Testing NAR",
    "japan": "Testing JPN", "jpn": "Testing JPN",
    "korea": "Testing KOR", "kor": "Testing KOR",
    "taiwan": "Testing TWN", "twn": "Testing TWN",
    "hk": "Testing Hong Kong", "hong kong": "Testing Hong Kong",
    "hmi": "Core HMI / GBK", "gbk": "Core HMI / GBK",
    "media": "Media / Tuner (Entertainment)",
    "tuner": "Media / Tuner (Entertainment)",
    "entertainment": "Media / Tuner (Entertainment)",
    "app store": "App Store / 3rd Party",
    "phone connectivity": "Phone-Connectivity-SPI",
    "spi": "Phone-Connectivity-SPI",
    "applications": "WS Applications",
    "platform": "WS Platform",
    "system": "WS System",
    "failed": "FAIL", "failure": "FAIL", "failures": "FAIL",
    "passed": "PASS", "blocked": "BLOCKED", "aborted": "ABORTED",
}

WORKSTREAMS = ["WS Applications", "WS Platform", "WS System"]
WORKING_GROUPS = ["Navigation", "Digital Assistant", "Core HMI / GBK",
                  "Media / Tuner (Entertainment)", "App Store / 3rd Party",
                  "Phone-Connectivity-SPI"]