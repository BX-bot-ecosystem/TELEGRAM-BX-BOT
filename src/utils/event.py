from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
from utils import config

with open(config.ROOT + '/credentials.json') as f:
    calendar_id = json.load(f)["calendar id"]
# The scopes define the level of access your bot will have to the shared calendar.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Path to the service account key JSON file.
SERVICE_ACCOUNT_KEY_PATH = config.ROOT + '/service_account.json'
def get_calendar_service():
    # Load the service account credentials from the JSON key file.
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_PATH, scopes=SCOPES)

    # Create the Calendar API client using the service account credentials.
    service = build("calendar", "v3", credentials=credentials)
    return service

def timeFormat(date, startTime):
    return "2023" + '-' + date["month"] + '-' + date["day"] + 'T' +

def create_event(service, date, startTime, endTime, color, committee, description):
    event_data={
        "summary": description,
        "start": {
            "dateTime": timeFormat(date, startTime)
        }
    }
    # Use the service to create an event in the shared calendar.
    event = service.events().insert(calendarId=calendar_id, body=event_data).execute()
    return event

def get_events(service):
    # Use the service to retrieve events from the shared calendar.
    events_result = service.events().list(calendarId=calendar_id, maxResults=10).execute()
    events = events_result.get("items", [])
    return events

event_data = {
        "summary": "Color Id 2",
        "start": {
            "dateTime": "2023-08-1T15:00:00",
            "timeZone": "Europe/Paris",  # Replace with the timezone of the event's start time.
        },
        "end": {
            "dateTime": "2023-08-1T17:00:00",
            "timeZone": "Europe/Paris",  # Replace with the timezone of the event's end time.
        },
        "extendedProperties": {
            "shared": {
                "committee": ".9 Bar"
            }
        },
    "colorId": '11'
    }

COLOR_ID = {'Lavender': '1',
          'Sage': '2',
          'Grape':'3',
          'Flamingo': '4',
          'Banana': '5',
          'Tangerine': '6',
          'Peacock': '7',
          'Graphite': '8',
          'Blueberry': '9',
          'Basil': '10',
          'Tomato': '11'
          }



create_event(get_calendar_service(), event_data=event_data)