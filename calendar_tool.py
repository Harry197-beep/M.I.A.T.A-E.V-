import os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]


def get_google_service(service_name, version):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(service_name, version, credentials=creds)


def get_upcoming_events(days_ahead=7, max_results=10):
    service = get_google_service("calendar", "v3")

    now = datetime.now(timezone.utc).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()

    events_result = service.events().list(
        calendarId="primary", timeMin=now, timeMax=future,
        maxResults=max_results, singleEvents=True, orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    if not events:
        return "No upcoming events found."

    summaries = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        summaries.append(f"{start}: {event.get('summary', '(no title)')}")

    return "\n".join(summaries)


def create_event(summary, start_datetime, end_datetime=None, timezone_str="Asia/Jakarta"):
    """
    Create a calendar event.
    start_datetime and end_datetime should be ISO format, e.g. '2026-08-13T10:00:00'
    If end_datetime not given, defaults to 1 hour after start.
    """
    service = get_google_service("calendar", "v3")

    if not end_datetime:
        start_dt = datetime.fromisoformat(start_datetime)
        end_datetime = (start_dt + timedelta(hours=1)).isoformat()

    event = {
        "summary": summary,
        "start": {"dateTime": start_datetime, "timeZone": timezone_str},
        "end": {"dateTime": end_datetime, "timeZone": timezone_str},
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: {created_event.get('summary')} at {created_event.get('start', {}).get('dateTime')} (link: {created_event.get('htmlLink')})"


if __name__ == "__main__":
    print(get_upcoming_events())
