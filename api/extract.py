from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

app = Flask(__name__)


# =========================================================
# Utility Functions
# =========================================================

def validate_url(url):
    parsed = urlparse(url)
    return parsed.scheme and parsed.netloc



def detect_framework(html_text, js_files):

    framework = "Unknown"

    html_lower = html_text.lower()

    # HTML detection
    if "vite" in html_lower:
        framework = "Vite"

    elif "__next" in html_lower:
        framework = "Next.js"

    elif "webpack" in html_lower:
        framework = "Webpack"

    elif "react" in html_lower:
        framework = "React"

    elif "vue" in html_lower:
        framework = "Vue"

    # JS filename detection
    for js in js_files:

        lower = js.lower()

        if "vite" in lower:
            framework = "Vite"
            break

        elif "webpack" in lower:
            framework = "Webpack"
            break

        elif "next" in lower:
            framework = "Next.js"
            break

        elif "react" in lower:
            framework = "React"
            break

        elif "vue" in lower:
            framework = "Vue"
            break

    return framework



def clean_sort(items):
    return sorted(list(set(items)))


# =========================================================
# Routes
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "name": "FF Web Event Asset Extractor API",
        "status": "running",
        "version": "1.0.0",
        "developer": "Chirantan"
    })


@app.route("/extract")
def extract_assets():

    target = request.args.get("url")

    # =====================================================
    # Validate URL
    # =====================================================

    if not target:

        return jsonify({
            "success": False,
            "error": {
                "code": 400,
                "message": "Missing URL parameter"
            }
        }), 400


    if not validate_url(target):

        return jsonify({
            "success": False,
            "error": {
                "code": 400,
                "message": "Invalid URL"
            }
        }), 400


    # =====================================================
    # Start Timer
    # =====================================================

    start_time = time.time()


    try:

        # =================================================
        # Browser Headers
        # =================================================

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": target
        }


        # =================================================
        # Request Website
        # =================================================

        response = requests.get(
            target,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )


        status_code = response.status_code


        # =================================================
        # Handle HTTP Errors
        # =================================================

        if status_code >= 400:

            return jsonify({
                "success": False,
                "error": {
                    "code": status_code,
                    "message": f"Website returned HTTP {status_code}"
                }
            }), status_code


        # =================================================
        # Parse HTML
        # =================================================

        soup = BeautifulSoup(response.text, "html.parser")


        # =================================================
        # Asset Containers
        # =================================================

        javascript_files = []
        stylesheet_files = []
        preload_files = []
        icon_files = []


        # =================================================
        # Extract JavaScript
        # =================================================

        for script in soup.find_all("script"):

            src = script.get("src")

            if src:

                full_url = urljoin(target, src)
                javascript_files.append(full_url)


        # =================================================
        # Extract LINK Assets
        # =================================================

        for link in soup.find_all("link"):

            href = link.get("href")

            if not href:
                continue

            full_url = urljoin(target, href)

            rel = link.get("rel")
            rel_text = " ".join(rel).lower() if rel else ""


            # Stylesheets
            if "stylesheet" in rel_text:
                stylesheet_files.append(full_url)


            # Preloads
            if "preload" in rel_text or "modulepreload" in rel_text:
                preload_files.append(full_url)


            # Icons
            if "icon" in rel_text:
                icon_files.append(full_url)


        # =================================================
        # Clean & Sort
        # =================================================

        javascript_files = clean_sort(javascript_files)
        stylesheet_files = clean_sort(stylesheet_files)
        preload_files = clean_sort(preload_files)
        icon_files = clean_sort(icon_files)


        # =================================================
        # Framework Detection
        # =================================================

        framework = detect_framework(
            response.text,
            javascript_files
        )


        # =================================================
        # Asset Counts
        # =================================================

        javascript_count = len(javascript_files)
        stylesheet_count = len(stylesheet_files)
        preload_count = len(preload_files)
        icon_count = len(icon_files)

        total_assets = (
            javascript_count
            + stylesheet_count
            + preload_count
            + icon_count
        )


        # =================================================
        # Response Time
        # =================================================

        end_time = time.time()
        response_time = round(end_time - start_time, 2)


        # =================================================
        # Final JSON Response
        # =================================================

        return jsonify({

            "success": True,

            "meta": {
                "site": urlparse(target).netloc,
                "framework": framework,
                "status": status_code,
                "response_time": f"{response_time}s",
                "total_assets": total_assets
            },

            "counts": {
                "javascript": javascript_count,
                "stylesheets": stylesheet_count,
                "preloads": preload_count,
                "icons": icon_count
            },

            "assets": {
                "javascript": javascript_files,
                "stylesheets": stylesheet_files,
                "preloads": preload_files,
                "icons": icon_files
            }

        })


    # =====================================================
    # Timeout Error
    # =====================================================

    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "error": {
                "code": 408,
                "message": "Request timed out"
            }
        }), 408


    # =====================================================
    # Connection Error
    # =====================================================

    except requests.exceptions.ConnectionError:

        return jsonify({
            "success": False,
            "error": {
                "code": 503,
                "message": "Connection failed"
            }
        }), 503


    # =====================================================
    # Unknown Error
    # =====================================================

    except Exception as e:

        return jsonify({
            "success": False,
            "error": {
                "code": 500,
                "message": str(e)
            }
        }), 500


# =========================================================
# Run App
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)