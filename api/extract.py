from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

@app.route("/")
def home():
    return "JS Extractor API Running"

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

        for script in soup.find_all("script"):

            src = script.get("src")

            if src:
                full = urljoin(target, src)

                if full.endswith(".js") or ".js" in full:
                    js_files.append(full)

        return jsonify({
            "success": True,
            "count": len(js_files),
            "js": js_files
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
