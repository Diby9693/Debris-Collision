import urllib.request
import json
import time
import subprocess
import os

print("--- Testing Local Web Server on Port 8080 ---")
try:
    resp = urllib.request.urlopen("http://localhost:8080/index.html")
    html = resp.read().decode('utf-8')
    print(f"[SUCCESS] index.html loaded: {len(html)} bytes, Status: {resp.status}")
    assert "ASTRO-GUARD // AI ORBITAL DEFENSE" in html
    assert "btn-theme-toggle" in html
    assert "btn-toggle-left-pane" in html
    assert "btn-mission-chandrayaan" in html
    assert "collision-alert-toast" in html
    assert "chandrayaan-hud" in html
    assert "ai-copilot-container" in html
    print("[SUCCESS] All required UI elements present in index.html!")
except Exception as e:
    print(f"[FAIL] Error loading index.html: {e}")

try:
    resp2 = urllib.request.urlopen("http://localhost:8080/standalone.html")
    html2 = resp2.read().decode('utf-8')
    print(f"[SUCCESS] standalone.html loaded: {len(html2)} bytes, Status: {resp2.status}")
    assert "window.EMBEDDED_AUDIO" in html2
    assert "AIAssistant" in html2
    assert "startChandrayaanMission" in html2
    print("[SUCCESS] standalone.html is completely bundled and contains embedded audio!")
except Exception as e:
    print(f"[FAIL] Error loading standalone.html: {e}")
