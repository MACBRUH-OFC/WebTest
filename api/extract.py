from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

@app.route("/")
def home():
    return "Asset Extractor API Running"

@app.route("/extract")
def extract():

    target = request.args.get("url")

    if not target:
        return jsonify({
            "error": "Missing URL"
        })

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            target,
            headers=headers,
            timeout=20
        )

        soup = BeautifulSoup(response.text, "html.parser")

        js_files = []
        css_files = []
        preload_files = []
        icons = []

        # Extract JS
        for script in soup.find_all("script"):

            src = script.get("src")

            if src:
                full = urljoin(target, src)

                if full not in js_files:
                    js_files.append(full)

        # Extract CSS
        for link in soup.find_all("link"):

            href = link.get("href")
            rel = link.get("rel")

            if not href:
                continue

            full = urljoin(target, href)

            rel_text = " ".join(rel).lower() if rel else ""

            # CSS
            if "stylesheet" in rel_text:
                if full not in css_files:
                    css_files.append(full)

            # Preload
            if "preload" in rel_text or "modulepreload" in rel_text:
                if full not in preload_files:
                    preload_files.append(full)

            # Icons
            if "icon" in rel_text:
                if full not in icons:
                    icons.append(full)

        return jsonify({
            "success": True,

            "js_count": len(js_files),
            "css_count": len(css_files),
            "preload_count": len(preload_files),

            "js": js_files,
            "css": css_files,
            "preload": preload_files,
            "icons": icons
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
