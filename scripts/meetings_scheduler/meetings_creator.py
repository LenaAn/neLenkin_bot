from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from pathlib import Path


from google.oauth2 import service_account
from googleapiclient.discovery import build

from zoom_meetings_creator import create_meeting

load_dotenv()
CLIENT_EMAIL = os.getenv("ZOOM_CLIENT_EMAIL")

CURR_DIR = Path(__file__).parent
SERVICE_ACCOUNT_FILE = CURR_DIR / "google_calendar.auth.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def create_calendar_event(
    summary: str,
    description: str,
    start_time: datetime,
    duration_minutes: int,
    attendees: list[str] = None,
):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )

    service = build("calendar", "v3", credentials=credentials)

    end_time = start_time + timedelta(minutes=duration_minutes)

    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
        "attendees": [{"email": email} for email in (attendees or [])],
    }

    event = service.events().insert(
        calendarId=CLIENT_EMAIL,
        body=event,
    ).execute()

    return event


def schedule_zoom_and_calendar(topic: str, start_time: str):
    zoom_meeting = create_meeting(topic, start_time)

    zoom_start_time = datetime.fromisoformat(
        zoom_meeting["start_time"].replace("Z", "")
    )

    calendar_event = create_calendar_event(
        summary=zoom_meeting["topic"],
        description=f"""
        Zoom Meeting
        
        Join URL: {zoom_meeting['join_url']}
        Meeting ID: {zoom_meeting['id']}
        """,
        start_time=zoom_start_time,
        duration_minutes=zoom_meeting["duration"],
    )

    return {
        "zoom": zoom_meeting,
        "calendar": calendar_event,
    }


if __name__ == "__main__":
    start_time = datetime(2026, 3, 5, 18, 0, 0).isoformat()
    event = schedule_zoom_and_calendar("DDIA-5", start_time)
    print(f"{event=}")
