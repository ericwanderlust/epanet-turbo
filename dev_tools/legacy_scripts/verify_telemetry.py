import requests
import os
import socket
import platform
import json
import time

def verify_telemetry():
    print("--- 🚀 EPANET-Turbo Telemetry Verification ---")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Local Identity
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "Unknown"
    
    print(f"🏠 Local IP: {local_ip} ({hostname})")
    
    # 2. Public IP Check
    print("... Detecting Public IP (this may take a few seconds) ...")
    try:
        public_ip = requests.get('https://api.ipify.org', timeout=5).text
    except:
        try:
            public_ip = requests.get('https://ifconfig.me/ip', timeout=5).text
        except:
            public_ip = "Unknown (Blocked)"
            
    print(f"🌏 Public IP: {public_ip}")
    
    # 3. Payload Construction
    data = {
        'hostname': hostname,
        'local_ip': local_ip,
        'public_ip': public_ip,
        'user': os.getenv('USERNAME') or os.getlogin(),
        'os': platform.platform(),
        'version': '2.0.0-VERIFY'
    }
    
    # 4. Sending to Proxy
    print("... Sending heartbeat to Cloudflare Worker ...")
    url = 'https://epanet-proxy.syhex40.workers.dev/notify'
    
    try:
        resp = requests.post(url, json=data, timeout=10)
        print(f"✅ Response Status: {resp.status_code}")
        print(f"✅ Response Body: {resp.text}")
        if resp.status_code == 200:
            print("\n🎉 Telemetry SUCCESS! Please check your Telegram for the message.")
        else:
            print("\n⚠️  Telemetry Sent but Worker returned error.")
            
    except Exception as e:
        print(f"\n❌ Sending Failed: {e}")
        print("💡 Suggestion: If you are in China, you may need a proxy.")
        print("   Powershell: $env:HTTPS_PROXY='http://127.0.0.1:7890'")
        print("   CMD: set HTTPS_PROXY=http://127.0.0.1:7890")

if __name__ == "__main__":
    verify_telemetry()

