from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

from zoom_meetings_creator import create_meeting
from meeting_saver import insert_scheduled_part_message
import constants

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
    return zoom_meeting, calendar_event


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: uv run meetings_creator.py <course_id> <year> <month> <day> <hour> <number of events>")
        sys.exit(1)
    course_id = int(sys.argv[1])
    first_meeeting_day = datetime(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
    number_of_events = int(sys.argv[6])

    for i in range(number_of_events):
        start_time = first_meeeting_day + (i * timedelta(7))
        zoom_meeting, calendar_event = schedule_zoom_and_calendar(f"Zoom for {constants.id_to_course[course_id]}",
                                                                  start_time.isoformat())

        insert_scheduled_part_message(
            week_number=start_time.isocalendar()[1],
            course_id=course_id,
            text=zoom_meeting["join_url"]
        )
        print(f"{zoom_meeting['join_url']} created!")

    print(f"{number_of_events} events created!")
