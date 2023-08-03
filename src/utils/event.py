from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
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

def format_date(date_obj):
    # Get the day of the week (e.g., Monday, Tuesday, etc.)
    day_of_week = date_obj.strftime("%A")

    # Get the day of the month with suffix (e.g., 1st, 2nd, 3rd, 4th, etc.)
    day_of_month = date_obj.strftime("%d")
    day_of_month = day_of_month if day_of_month[0] != '0' else day_of_month[1]
    suffix = "th" if 11 <= int(day_of_month) % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(int(day_of_month) % 10, "th")

    # Get the month (e.g., January, February, etc.)
    month = date_obj.strftime("%B")

    # Combine the parts to create the formatted date string
    formatted_date = f"{day_of_week} {day_of_month}{suffix} of {month}"

    return formatted_date

def timeFormat(date, time):

    return str(date) + 'T' + time[0] + ':' + time[1] + ':00'

def create_event(date, startTime, endTime, committee, description):
    service = get_calendar_service()
    event_data={
        "summary": description,
        "start": {
            "dateTime": timeFormat(date, startTime),
            "timeZone": "Europe/Paris",
        },
        "end": {
            "dateTime": timeFormat(date, endTime),
            "timeZone": "Europe/Paris",
        },
        "extendedProperties": {
            "shared": {
                "committee": committee
            }
        },
        "colorId": color_from_committee(committee)
    }
    # Use the service to create an event in the shared calendar.
    event = service.events().insert(calendarId=calendar_id, body=event_data).execute()
    return event

def get_events(service):
    # Use the service to retrieve events from the shared calendar.
    events_result = service.events().list(calendarId=calendar_id, maxResults=10).execute()
    events = events_result.get("items", [])
    return events

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


def color_from_committee(committee_name):
    """
    A simple hash from the committee_name to a number from 0 to 11 which represents the color of the event in the calendar
    """
    value = 0
    for character in committee_name:
        value += ord(character)
    colorID = value%12
    return str(colorID)