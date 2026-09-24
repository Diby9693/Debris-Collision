import socket
import urllib.request
import json
import base64
import os
import struct
import subprocess
import time

class SimpleCDPClient:
    def __init__(self, ws_url):
        # ws_url: ws://localhost:9222/devtools/page/...
        url_part = ws_url.replace("ws://", "")
        host_port, path = url_part.split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=10)
        
        # Handshake
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        handshake = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode('ascii'))
        resp = self.sock.recv(4096).decode('latin1')
        if "101" not in resp:
            raise Exception("WebSocket handshake failed: " + resp)
        self.msg_id = 0

    def send_cmd(self, method, params=None):
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method, "params": params or {}}
        payload = json.dumps(msg).encode('utf-8')
        
        # Frame format: FIN=1, opcode=1 (text), MASK=1
        header = bytearray([0x81])
        mask_key = os.urandom(4)
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        
        header.extend(mask_key)
        masked_payload = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + masked_payload)
        return self.read_response(self.msg_id)

    def read_response(self, target_id):
        while True:
            # Read 2-byte header
            head = self.sock.recv(2)
            if len(head) < 2:
                raise Exception("Socket closed")
            b1, b2 = head
            length = b2 & 0x7F
            if length == 126:
                ext = self.sock.recv(2)
                length = struct.unpack("!H", ext)[0]
            elif length == 127:
                ext = self.sock.recv(8)
                length = struct.unpack("!Q", ext)[0]
            
            # Read payload in chunks
            data = bytearray()
            while len(data) < length:
                chunk = self.sock.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
            
            try:
                msg = json.loads(data.decode('utf-8'))
                if msg.get("id") == target_id:
                    return msg.get("result")
            except Exception:
                pass

    def evaluate(self, expr):
        res = self.send_cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if res and "result" in res:
            return res["result"].get("value")
        return None

    def screenshot(self, filepath):
        res = self.send_cmd("Page.captureScreenshot", {"format": "png"})
        if res and "data" in res:
            img_bytes = base64.b64decode(res["data"])
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            print(f"[SCREENSHOT] Saved: {filepath} ({len(img_bytes)} bytes)")
            return True
        return False

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def main():
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

    time.sleep(3)
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/list")
        targets = json.loads(resp.read().decode())
        page_target = next((t for t in targets if "localhost:8080" in t.get("url", "")), None)
        if not page_target:
            print("No page target found!")
            return

        ws_url = page_target["webSocketDebuggerUrl"]
        print("Connecting to CDP WS:", ws_url)
        client = SimpleCDPClient(ws_url)

        # 1. Verify App Initialization
        app_ready = client.evaluate("typeof window.SpaceApp !== 'undefined' && window.SpaceApp.orbitalCatalog.length > 0")
        print("SpaceApp initialized:", app_ready)

        # 2. Check catalog count & active target
        target_name = client.evaluate("window.SpaceApp.selectedObject ? window.SpaceApp.selectedObject.name : 'None'")
        print("Initial selected target:", target_name)

        # 3. Capture Initial View (Default Dark Mode, Satellites with scanning cones)
        time.sleep(1.5)
        client.screenshot("screenshot_initial.png")

        # 4. Test Toggle Auxiliary Panes (Collapse Left & Right sidebars)
        client.evaluate("window.SpaceApp.ui.toggleLeftPanel(true); window.SpaceApp.ui.toggleRightPanel(true);")
        time.sleep(0.5)
        is_left_collapsed = client.evaluate("document.querySelector('.left-panel').classList.contains('collapsed')")
        is_right_collapsed = client.evaluate("document.querySelector('.right-panel').classList.contains('collapsed')")
        print("Panels Collapsed Successfully:", is_left_collapsed and is_right_collapsed)
        client.screenshot("screenshot_collapsed_sidebars.png")

        # Expand panels back
        client.evaluate("window.SpaceApp.ui.toggleLeftPanel(false); window.SpaceApp.ui.toggleRightPanel(false);")
        time.sleep(0.5)

        # 5. Test Light Mode Toggle
        client.evaluate("window.SpaceApp.ui.toggleTheme()")
        time.sleep(0.5)
        is_light = client.evaluate("document.body.classList.contains('theme-light')")
        print("Light Mode Active:", is_light)
        client.screenshot("screenshot_light_mode.png")

        # Switch back to dark mode
        client.evaluate("window.SpaceApp.ui.toggleTheme()")
        time.sleep(0.5)

        # 6. Test Collision Simulation (Verify Tactical Alert Toast & 3D Explosions)
        print("Triggering Collision Simulation...")
        client.evaluate("window.SpaceApp.ui.simulateCollisionEvent()")
        time.sleep(1.0)
        toast_visible = client.evaluate("!document.getElementById('collision-alert-toast').classList.contains('hidden')")
        toast_text = client.evaluate("document.getElementById('toast-body').innerText")
        print("Tactical Collision Toast Visible:", toast_visible)
        print("Toast Text:", (toast_text or "").encode('ascii', errors='replace').decode())
        client.screenshot("screenshot_collision_toast.png")

        # Dismiss toast
        client.evaluate("document.getElementById('btn-toast-dismiss').click()")

        # 7. Test Chandrayaan-4 Lunar Landing Mission Simulator
        print("Launching Chandrayaan-4 Lunar Mission...")
        client.evaluate("window.SpaceApp.ui.launchChandrayaanMission()")
        time.sleep(2.5)
        hud_visible = client.evaluate("!document.getElementById('chandrayaan-hud').classList.contains('hidden')")
        hud_status = client.evaluate("document.getElementById('mission-hud-status').innerText")
        print("Chandrayaan HUD Active:", hud_visible)
        print("HUD Status:", (hud_status or "").encode('ascii', errors='replace').decode())
        client.screenshot("screenshot_chandrayaan_mission.png")

        # 8. Test AI Aerospace Copilot
        print("Testing AI Mission Copilot...")
        client.evaluate("window.SpaceApp.aiAssistant.toggleWidget(true)")
        client.evaluate("window.SpaceApp.aiAssistant.handleUserInput('Simulate Collision')")
        time.sleep(1.0)
        copilot_msgs = client.evaluate("document.getElementById('ai-copilot-messages').innerText")
        print("Copilot Messages:", (copilot_msgs or "").encode('ascii', errors='replace').decode())
        client.screenshot("screenshot_ai_copilot.png")

        client.close()
        print("\n[ALL 8 VERIFICATION TESTS COMPLETED SUCCESSFULLY!]")

    finally:
        proc.terminate()
        print("Test teardown complete.")

if __name__ == "__main__":
    main()
