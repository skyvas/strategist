"""
Storefront & E-Commerce Integration Test Suite
Agent Roles: QA Adversary (Loop A) & DevOps Auditor (Loop B)
Project: Kairi & Co. Storefront Mockup with GitHub Pages & Mobile Compatibility
"""

import os
import urllib.request
import re
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "client", "static-mockup"))
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_static_files_exist():
    required_files = [
        "index.html",
        "product.html",
        "shop.html",
        "story.html",
        "404.html",
        "styles.css",
        "app.js"
    ]
    for filename in required_files:
        filepath = os.path.join(BASE_DIR, filename)
        assert os.path.exists(filepath), f"Missing file: {filename}"
        assert os.path.getsize(filepath) > 400, f"File {filename} is suspiciously small or empty"
    print("✓ All core storefront files (including 404.html fallback) exist and are populated.")

def test_image_assets_exist():
    required_images = [
        "hero_banner.jpg",
        "classic_kairi.jpg",
        "andhra_fire.jpg",
        "hot_honey_mango.jpg",
        "smoked_garlic.jpg",
        "tasting_box.jpg",
        "grilled_cheese.jpg",
        "avocado_toast.jpg"
    ]
    img_dir = os.path.join(BASE_DIR, "images")
    assert os.path.exists(img_dir), "images/ directory missing"
    for img in required_images:
        path = os.path.join(img_dir, img)
        assert os.path.exists(path), f"Missing image asset: {img}"
        assert os.path.getsize(path) > 10000, f"Image {img} size too small"
    print("✓ All high-res culinary image assets exist and verified.")

class MockDirectoryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress console noise during test run

def test_http_endpoints_200():
    # Find free port for test server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        test_port = s.getsockname()[1]

    server = HTTPServer(('127.0.0.1', test_port), MockDirectoryHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{test_port}"
    endpoints = [
        "/index.html",
        "/product.html",
        "/shop.html",
        "/story.html",
        "/404.html",
        "/styles.css",
        "/app.js",
        "/images/classic_kairi.jpg"
    ]
    for endpoint in endpoints:
        url = base_url + endpoint
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5) as res:
            assert res.status == 200, f"Endpoint {url} returned status {res.status}"
    
    server.shutdown()
    print("✓ Embedded test server verified 200 OK across all routes and assets.")

def test_html_semantic_and_mobile_structures():
    pages = ["index.html", "product.html", "shop.html", "story.html"]
    for p in pages:
        with open(os.path.join(BASE_DIR, p), "r", encoding="utf-8") as f:
            content = f.read()
        assert "<!DOCTYPE html>" in content, f"{p} missing DOCTYPE"
        assert "<title>" in content, f"{p} missing title"
        assert "styles.css" in content, f"{p} missing styles link"
        assert "app.js" in content, f"{p} missing app.js script"
        assert "cart-drawer" in content, f"{p} missing slide-out cart drawer structure"
        # Mobile ergonomics assertions
        assert "viewport-fit=cover" in content, f"{p} missing viewport-fit=cover"
        assert "mobile-nav-toggle" in content, f"{p} missing mobile navigation hamburger toggle"
        assert "mobile-nav-drawer" in content, f"{p} missing mobile navigation drawer"
    print("✓ All pages contain proper semantic structures, cart drawer, and mobile navigation.")

def test_product_catalog_and_temp_db_engine():
    with open(os.path.join(BASE_DIR, "app.js"), "r", encoding="utf-8") as f:
        js = f.read()
    assert "FREE_SHIPPING_THRESHOLD = 50.00" in js, "Free shipping threshold mismatch"
    assert "classic-kairi" in js, "Classic Kairi product key missing"
    assert "andhra-fire" in js, "Andhra Fire product key missing"
    assert "hot-honey-mango" in js, "Hot Honey Mango product key missing"
    assert "smoked-garlic" in js, "Smoked Garlic & Chilli product key missing"
    assert "tasting-box" in js, "Tasting Box bundle missing"
    # Temp DB assertions
    assert "KairiTempDB" in js, "KairiTempDB engine missing from app.js"
    assert "document.cookie" in js, "Cookie persistence missing from KairiTempDB"
    assert "sessionStorage" in js, "sessionStorage fallback missing from KairiTempDB"
    assert "localStorage" in js, "localStorage missing from KairiTempDB"
    assert "openMobileNav" in js, "openMobileNav function missing from app.js"
    assert "closeMobileNav" in js, "closeMobileNav function missing from app.js"
    print("✓ Product catalog, business rules, mobile operations, and KairiTempDB verified in app.js.")

def test_styles_mobile_compatibility():
    with open(os.path.join(BASE_DIR, "styles.css"), "r", encoding="utf-8") as f:
        css = f.read()
    assert "safe-area-inset-top" in css, "safe-area-inset-top missing from styles.css"
    assert "safe-area-inset-bottom" in css, "safe-area-inset-bottom missing from styles.css"
    assert "100dvh" in css, "100dvh dynamic viewport height missing from styles.css"
    assert "mobile-nav-drawer" in css, "mobile-nav-drawer styles missing from styles.css"
    assert "mobile-nav-toggle" in css, "mobile-nav-toggle styles missing from styles.css"
    assert "touch-action: manipulation" in css, "touch-action manipulation missing from styles.css"
    assert "-webkit-tap-highlight-color" in css, "tap highlight color reset missing"
    assert "font-size: 16px !important" in css, "iOS Safari auto-zoom prevention rule missing"
    print("✓ CSS safe areas, 100dvh viewport height, and iOS/Android touch rules verified.")

def test_github_pages_deployment_artifacts():
    nojekyll_path = os.path.join(BASE_DIR, ".nojekyll")
    assert os.path.exists(nojekyll_path), ".nojekyll missing from static-mockup"

    script_path = os.path.join(REPO_ROOT, "scripts", "deploy-gh-pages.sh")
    assert os.path.exists(script_path), "scripts/deploy-gh-pages.sh missing"
    assert os.access(script_path, os.X_OK), "scripts/deploy-gh-pages.sh is not executable"
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    assert "BRANCH_NAME=\"gh-pages\"" in script, "gh-pages branch target missing in script"
    assert ".nojekyll" in script, ".nojekyll copy missing in script"
    print("✓ GitHub Pages gh-pages branch deployment architecture and .nojekyll verified.")

if __name__ == "__main__":
    print("--- RUNNING QA ADVERSARY (LOOP A) & DEVOPS AUDITOR (LOOP B) VERIFICATION ---")
    test_static_files_exist()
    test_image_assets_exist()
    test_http_endpoints_200()
    test_html_semantic_and_mobile_structures()
    test_product_catalog_and_temp_db_engine()
    test_styles_mobile_compatibility()
    test_github_pages_deployment_artifacts()
    print("--- ALL VERIFICATION TESTS PASSED (100% SUCCESS) ---")
