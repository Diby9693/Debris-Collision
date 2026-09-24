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
        url_part = ws_url.replace("ws://", "")
        host_port, path = url_part.split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=10)
        
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
            raise Exception("Handshake failed: " + resp)
        self.msg_id = 0

    def send_cmd(self, method, params=None):
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method, "params": params or {}}
        payload = json.dumps(msg).encode('utf-8')
        
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
            head = self.sock.recv(2)
            if len(head) < 2:
                return None
            b1, b2 = head
            length = b2 & 0x7F
            if length == 126:
                ext = self.sock.recv(2)
                length = struct.unpack("!H", ext)[0]
            elif length == 127:
                ext = self.sock.recv(8)
                length = struct.unpack("!Q", ext)[0]
            
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
                elif msg.get("method") == "Runtime.consoleAPICalled":
                    args = msg.get("params", {}).get("args", [])
                    print("[CONSOLE LOG]", [a.get("value") for a in args])
                elif msg.get("method") == "Runtime.exceptionThrown":
                    exc = msg.get("params", {}).get("exceptionDetails", {})
                    print("[CONSOLE EXCEPTION]", exc.get("text"), exc.get("exception", {}).get("description"), "URL:", exc.get("url"), "Line:", exc.get("lineNumber"), "Col:", exc.get("columnNumber"))
            except Exception:
                pass

    def evaluate(self, expr):
        res = self.send_cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if res and "result" in res:
            return res["result"].get("value")
        return None

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
        client = SimpleCDPClient(ws_url)

        # Enable Console & Runtime domains
        client.send_cmd("Console.enable")
        client.send_cmd("Runtime.enable")

        # Wait a bit and check
        time.sleep(2)
        print("Checking readyState:", client.evaluate("document.readyState"))
        print("Checking window.SpaceApp:", client.evaluate("typeof window.SpaceApp"))
        print("Checking errors if any:", client.evaluate("window.__lastError || 'None'"))

        # Let's inspect scripts loaded
        scripts = client.evaluate("Array.from(document.querySelectorAll('script')).map(s => s.src)")
        print("Scripts on page:", scripts)

        time.sleep(1)

    finally:
        proc.terminate()

if __name__ == "__main__":
    main()
