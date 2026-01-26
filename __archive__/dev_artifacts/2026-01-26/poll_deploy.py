import requests
import time
import sys

URL = "https://rapidenergy.onrender.com/debug/gemini"

def poll_for_update():
    print(f"Polling {URL} for version 1.1.0...")
    for i in range(120):  # 120 attempts / 5s = 10 minutes max
        try:
            r = requests.get(URL, timeout=5)
            data = r.json()
            
            version = data.get("version", "unknown")
            engine_status = data.get("gemini_configured", "UNKNOWN")
            
            sys.stdout.write(f"\rAttempt {i+1}: Version={version} | GeminiEnv={engine_status}   ")
            sys.stdout.flush()
            
            if r.status_code == 200:
                print("\n\n✅ DEBUG ENDPOINT ALIVE!")
                print("--------------------------------------------------")
                print(json.dumps(data, indent=2))
                print("--------------------------------------------------")
                return
            
        except Exception as e:
            pass
        
        time.sleep(5)

    print("\n❌ Timeout waiting for deploy.")

if __name__ == "__main__":
    poll_for_update()
