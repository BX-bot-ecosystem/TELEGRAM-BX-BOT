import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from utils import config
import json

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

def create_event(service, event_data):
    # Use the service to create an event in the shared calendar.
    event = service.events().insert(calendarId=calendar_id, body=event_data).execute()
    return event

def get_events(service):
    # Use the service to retrieve events from the shared calendar.
    events_result = service.events().list(calendarId=calendar_id, maxResults=10).execute()
    events = events_result.get("items", [])
    return events

# Other methods for updating and deleting events can also be implemented.

def main():
    # Get the Calendar API service with the service account credentials.
    service = get_calendar_service()

    # Create or retrieve events from the shared calendar.
    events = get_events(service)
    for event in events:
        print(event["summary"])

if __name__ == "__main__":
    main()