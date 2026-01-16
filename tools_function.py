import datetime
import json
import os
from dotenv import load_dotenv
import requests
from langchain_core.tools import tool

load_dotenv()

CALENDLY_TOKEN = os.getenv("CALENDLY_TOKEN")
CALENDLY_USER = os.getenv("CALENDLY_API_URI")


@tool
def get_current_time():
    """Retrieves the current time"""
    today = datetime.datetime.now()
    day_name = today.strftime("%A")
    return "Current time: " + day_name + " and the day today is : " + day_name


@tool
def get_day_from_date(year, month, day):
    """Retrieves the day of the given date

    Args:
        year (int): the year
        month (int): the month
        day (int): the day
    """
    date_obj = datetime.date(year, month, day)
    weekday_name = date_obj.strftime("%A")
    return str(weekday_name)


def get_all_events():
    """Retrieves all meeting types of the owner, these are used to help decide which type of meeting to make."""
    url = "https://api.calendly.com/event_types"
    print("1")
    params = {"user": CALENDLY_USER}
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CALENDLY_TOKEN,
    }
    response = requests.request("GET", url, headers=headers, params=params)

    json = response.json()
    all_events = [
        "Calendly lets users set events which is essentially a template for a meeting thats pre-configured to allow easy bookings, below are all the meeting templates made by the host that you work for"
    ]
    for i in range(len(json["collection"])):
        # locations is an array itself, will need to change it to a for loop later
        all_events.append(
            "name of the meeting type: "
            + json["collection"][i]["name"]
            + " ,duration of the meeting: "
            + str(json["collection"][i]["duration"])
            + " ,other possible durations: "
            + str(json["collection"][i]["duration_options"])
            + " ,location of where to hold the meeting "
            + json["collection"][i]["locations"][0]["kind"]
            + " ,the link that is required to identify this meeting later: "
            + json["collection"][i]["uri"]
        )
    return "".join(all_events)


def busy_times():
    """Retrieves all the times the owner already has a meeting booked in"""
    url = "https://api.calendly.com/user_busy_times"
    params = {
        "start_time": "2026-01-12T20:00:00.000000Z",
        "end_time": "2026-01-14T20:30:00.000000Z",
        "user": CALENDLY_USER,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CALENDLY_TOKEN,
    }
    response = requests.request("GET", url, headers=headers, params=params)
    json = response.json()
    all_busy_times = [
        "These are the times the user is busy at and cannot schedule a meeting"
    ]
    for i in range(len(json["collection"])):
        all_busy_times.append(
            "end time of the meeting: "
            + str(json["collection"][i]["buffered_end_time"])
            + ", start time of the meeting: "
            + str(json["collection"][i]["buffered_start_time"])
        )
    return "".join(all_busy_times)


def total_avaliability():
    """Gets the total schedule of the owner, this shows when all a meeting can be booked, however it doesnt show
    times when meetings might already be booked, for that call busy_times"""
    url = "https://api.calendly.com/user_availability_schedules"

    params = {
        "user": CALENDLY_USER,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CALENDLY_TOKEN,
    }
    response = requests.request("GET", url, headers=headers, params=params)
    json = response.json()
    schedule = [
        "These are the days the person is avaliable to actually take a meeting on "
    ]
    for i in range(len(json["collection"])):
        for j in range(len(json["collection"][i]["rules"])):
            if (
                json["collection"][i]["rules"][j]["type"] == "wday"
                and len(json["collection"][i]["rules"][j]["intervals"]) == 0
            ):
                schedule.append(
                    ". Day : "
                    + json["collection"][i]["rules"][j]["wday"]
                    + ", there is no availability"
                )
            elif json["collection"][i]["rules"][j]["type"] == "wday":
                string = ""
                for k in range(len(json["collection"][i]["rules"][j]["intervals"])):
                    string = " and "
                    string += (
                        ", available from "
                        + str(json["collection"][i]["rules"][j]["intervals"][k]["from"])
                        + " to "
                        + str(json["collection"][i]["rules"][j]["intervals"][k]["to"])
                    )
                schedule.append(
                    ". Day : " + json["collection"][i]["rules"][j]["wday"] + string
                )
    return "".join(schedule)


@tool
def make_meeting(event_uri, start_time, name, email):
    """Use this function to make a booking on calendly.

    Args:
        event_uri: Takes in the event's uri so calendly knows which event type you'd want to book
        start_time: Takes in the start time of the meeting
        name: Takes in the name of the person wanting to book the meeting with the owner
        email: Takes in the email of the person wanting to book the meeting with the owner
    """

    print(event_uri, start_time, name, email)
    url = "https://api.calendly.com/invitees"
    body = {
        "event_type": event_uri,
        "start_time": start_time,
        "invitee": {
            "name": name,
            "email": email,
            "timezone": "Europe/London",
        },
        "location": {"kind": "google_conference"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CALENDLY_TOKEN,
    }
    try:
        response = requests.request("POST", url, headers=headers, json=body)
        print(response.status_code)
        print(response.json())
        if response.status_code == 429:
            return "FAIL, server responses with 429 status code, try again later"
        elif 200 <= response.status_code < 300:
            return "SUCCESS, The meeting has been scheduled"
        else:
            return "FAIL, The meeting could not be scheduled as theyre busy at that time, try another time"
    except Exception as e:
        print("Test2")
        return "FAIL, The meeting could not be scheduled as theyre busy at that time, try another time"


# print(
#     make_meeting(
#         event_uri="https://api.calendly.com/event_types/270830b6-86d2-42a7-938e-7662babc47c7",
#         start_time="2026-02-03T10:00:00Z",
#         name="Jugtej Singh",
#         email="jugtej3singh@gmail.com",
#     )
# )
