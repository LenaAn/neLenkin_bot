from datetime import datetime
import base64
import os

import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
CLIENT_EMAIL = os.getenv("ZOOM_CLIENT_EMAIL")


def get_access_token():
    url = "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=" + ACCOUNT_ID

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


def create_meeting(topic: str, start_time: str):
    access_token = get_access_token()

    url = f"https://api.zoom.us/v2/users/{CLIENT_EMAIL}/meetings"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "topic": topic,
        "type": 2,  # Scheduled meeting
        "start_time": start_time,
        "duration": 60,
        "timezone": "Europe/Berlin",
        "agenda": "Created automatically by nelenkin-bot",
        "settings": {
            "join_before_host": True,
            "approval_type": 2,  # no registration required
            "waiting_room": False
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    start_time = datetime(2026, 3, 5, 18, 0, 0).isoformat()
    meeting = create_meeting("DDIA-5", start_time)
    print(f"{meeting=}")
