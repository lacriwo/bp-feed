#!/usr/bin/env python3
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

DEFAULT_SOURCE_URL = (
    "https://api.macroserver.ru/estate/export/yandex/"
    "OzA5_WiGLTOJUuUfZsa-aAnYrqeYWBlO7q97bDXLcTWdInddefntJn-Gx9oKQ2qDosqdi_K_c8t7HhEqgVzInjUi_sG_3P3HqxDZrIROtRuZqBKBbk-f9dJwUSIHZkZnW3SzJXh8MTc2ODk3Nzc3MHxlZGZkMQ/"
    "394-yandex.xml?feed_id=8705"
)

SOURCE_URL = os.environ.get("SOURCE_FEED_URL", DEFAULT_SOURCE_URL).strip()
TARGET_URL = os.environ.get("TARGET_URL", "https://ligo-polyanka.ru").strip()
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "docs/bp-yandex-patched.xml").strip()

REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "90"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))


def fetch_xml(url: str, timeout: int, retries: int) -> bytes:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    raise RuntimeError(f"HTTP status {status}")
                return response.read()
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < retries:
                wait_sec = attempt * 3
                print(f"Fetch failed (attempt {attempt}/{retries}): {exc}. Retry in {wait_sec}s...")
                time.sleep(wait_sec)
            else:
                print(f"Fetch failed (attempt {attempt}/{retries}): {exc}")
    raise RuntimeError(f"Unable to fetch source feed after {retries} attempts: {last_error}")


xml_data = fetch_xml(SOURCE_URL, REQUEST_TIMEOUT, MAX_RETRIES)
root = ET.fromstring(xml_data)

ns_uri = ""
if root.tag.startswith("{") and "}" in root.tag:
    ns_uri = root.tag[1:root.tag.index("}")]

ns = {"n": ns_uri} if ns_uri else {}
offers = root.findall(".//n:offer" if ns_uri else ".//offer", ns)

for offer in offers:
    url_node = offer.find("n:url" if ns_uri else "url", ns)
    if url_node is None:
        # Если namespace есть, создаем тег с namespace, чтобы структура XML оставалась корректной
        tag = f"{{{ns_uri}}}url" if ns_uri else "url"
        url_node = ET.SubElement(offer, tag)
    url_node.text = TARGET_URL

if ns_uri:
    ET.register_namespace("", ns_uri)

output_dir = os.path.dirname(OUTPUT_FILE) or "."
os.makedirs(output_dir, exist_ok=True)
ET.ElementTree(root).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

print(f"Offers processed: {len(offers)}")
print(f"Source URL: {SOURCE_URL}")
print(f"Output file: {OUTPUT_FILE}")
