import requests
import time
import base64
from datetime import datetime
import cv2
import numpy as np

# === Firebase Settings ===
FIREBASE_TRIGGER_URL = "https://camera-fd1d5-default-rtdb.firebaseio.com/snapshotTrigger.json"
FIREBASE_IMAGE_URL = "https://camera-fd1d5-default-rtdb.firebaseio.com/latestSnapshot.json"

# === Stream Source (live video feed URL from Pi #1) ===
VIDEO_FEED_URL = "http://192.168.1.54:5000/video_feed"

# === Interval between trigger checks (seconds) ===
CHECK_INTERVAL = 2

# === Utility Functions ===
def fetch_frame():
    try:
        stream = requests.get(VIDEO_FEED_URL, stream=True)
        bytes_data = b""
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                return frame
    except Exception as e:
        print(f"[ERROR] Failed to fetch frame: {e}")
    return None

def upload_snapshot(image):
    _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    b64_image = base64.b64encode(buffer).decode('utf-8')
    payload = {
        "timestamp": datetime.now().strftime("%a, %d %B %Y %I:%M:%S %p"),
        "image": b64_image
    }
    try:
        res = requests.put(FIREBASE_IMAGE_URL, json=payload)
        if res.status_code == 200:
            print("[UPLOAD] Snapshot uploaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to upload snapshot: {e}")

def clear_trigger():
    try:
        requests.delete(FIREBASE_TRIGGER_URL)
    except Exception as e:
        print(f"[ERROR] Failed to clear trigger: {e}")

def check_trigger():
    try:
        res = requests.get(FIREBASE_TRIGGER_URL)
        if res.status_code == 200 and res.json() is True:
            print("[TRIGGER] Snapshot command received")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to check trigger: {e}")
    return False

# === Main Loop ===
def run_snapshot_listener():
    print("[SYSTEM] Snapshot listener started...")
    while True:
        if check_trigger():
            frame = fetch_frame()
            if frame is not None:
                upload_snapshot(frame)
            clear_trigger()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_snapshot_listener()
