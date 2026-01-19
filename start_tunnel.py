from pyngrok import ngrok
import time
import threading
import subprocess
import sys
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set ngrok auth token
ngrok_token = os.getenv("NGROK_AUTHTOKEN")
if ngrok_token:
    ngrok.set_auth_token(ngrok_token)
else:
    print("⚠️  WARNING: NGROK_AUTHTOKEN not found in .env")
    print("Please set your ngrok token in the .env file")
    sys.exit(1)

def run_flask_app():
    """Run the Flask app on port 3000"""
    try:
        # Run Flask app
        subprocess.run([sys.executable, "app.py"], cwd=".")
    except Exception as e:
        print(f"Flask Error: {e}")

def run_ngrok_tunnel():
    """Create ngrok tunnel after giving Flask time to start"""
    time.sleep(2)  # Wait for Flask to start
    try:
        public_url = ngrok.connect(3000).public_url
        print(f"\n{'='*50}")
        print(f"✅ PUBLIC URL: {public_url}")
        print(f"{'='*50}\n")
        
        # Keep tunnel alive
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
    except Exception as e:
        print(f"Tunnel Error: {e}")

# Start both in separate threads
flask_thread = threading.Thread(target=run_flask_app, daemon=False)
tunnel_thread = threading.Thread(target=run_ngrok_tunnel, daemon=False)

print("🚀 Starting Ramadan App with Public Tunnel...\n")

tunnel_thread.start()
flask_thread.start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n⛔ Shutting down...")
    ngrok.kill()
    sys.exit(0)
