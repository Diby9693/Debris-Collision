import subprocess
import time
import urllib.request
import json
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc = subprocess.Popen([
    chrome_path,
    "--headless=new",
    "--remote-debugging-port=9222",
    "--disable-gpu",
    "--no-sandbox",
    "--window-size=1600,1000",
    "http://localhost:8080/index.html"
])

print("Launched Chrome, waiting for CDP port...")
time.sleep(3)

try:
    resp = urllib.request.urlopen("http://localhost:9222/json/list")
    data = json.loads(resp.read().decode())
    print("CDP targets found:", len(data))
    for t in data:
        print(" -", t.get('title'), "|", t.get('url'))
finally:
    proc.terminate()
    print("Chrome terminated cleanly.")
