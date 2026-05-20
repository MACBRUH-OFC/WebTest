from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "FF Web Event Asset Extractor API Running"
    })


@app.route("/extract")
def extract():

    target = request.args.get("url")

    # Validate URL
    if not target:
        return jsonify({
            "success": False,
            "message": "Missing URL parameter"
        }), 400

    parsed = urlparse(target)

    if not parsed.scheme or not parsed.netloc:
        return jsonify({
            "success": False,
            "message": "Invalid URL"
        }), 400

    start_time = time.time()

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": target
        }

        response = requests.get(
            target,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )

        status_code = response.status_code

        # Block bad responses
        if status_code >= 400:
            return jsonify({
                "success": False,
                "status": status_code,
                "message": f"Website returned HTTP {status_code}"
            }), status_code

        soup = BeautifulSoup(response.text, "html.parser")

        js_files = []
        css_files = []
        preload_files = []
        icon_files = []

        framework = "Unknown"

        # -------------------------
        # Extract JS
        # -------------------------
        for script in soup.find_all("script"):

            src = script.get("src")

            if src:

                full = urljoin(target, src)

                if full not in js_files:
                    js_files.append(full)

                # Framework detection
                lower = full.lower()

                if "vite" in lower:
                    framework = "Vite"

                elif "webpack" in lower:
                    framework = "Webpack"

                elif "next" in lower:
                    framework = "Next.js"

                elif "react" in lower:
                    framework = "React"

        # -------------------------
        # Extract LINK assets
        # -------------------------
        for link in soup.find_all("link"):

            href = link.get("href")

            if not href:
                continue

            full = urljoin(target, href)

            rel = link.get("rel")
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

                if full not in icon_files:
                    icon_files.append(full)

        # -------------------------
        # Sorting
        # -------------------------
        js_files.sort()
        css_files.sort()
        preload_files.sort()
        icon_files.sort()

        total_assets = (
            len(js_files)
            + len(css_files)
            + len(preload_files)
            + len(icon_files)
        )

        end_time = time.time()

        response_time = round(end_time - start_time, 2)

        # -------------------------
        # Final Response
        # -------------------------
        return jsonify({

            "success": True,

            "meta": {
                "site": parsed.netloc,
                "status": status_code,
                "framework": framework,
                "response_time": f"{response_time}s",
                "total_assets": total_assets
            },

            "counts": {
                "javascript": len(js_files),
                "stylesheets": len(css_files),
                "icons": len(icon_files),
                "preloads": len(preload_files)
            },

            "assets": {
                "javascript": js_files,
                "stylesheets": css_files,
                "icons": icon_files,
                "preloads": preload_files
            }

        })

    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "message": "Request timed out"
        }), 408

    except requests.exceptions.ConnectionError:

        return jsonify({
            "success": False,
            "message": "Connection failed"
        }), 503

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
