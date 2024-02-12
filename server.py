from flask import Flask, jsonify, render_template
import requests
from ics import Calendar
from datetime import datetime, timedelta
import threading

app = Flask(__name__)

# Global variable to store the last fetch time
last_fetch_time = None

# A lock to prevent concurrent data fetches in a multithreaded environment
fetch_lock = threading.Lock()

# Replace the URL with the calendar URL you provided
calendar_url = "https://www.srisriravishankar.org/?post_type=tribe_events&ical=1&eventDisplay=list"

def split_into_main_and_full(input_string):
    # Split the string into parts, trying to split into three parts from the right
    parts = input_string.rsplit(',', 3)
    
    # If there are less than three parts, then the whole input string is the main_string
    if len(parts) <= 3:
        city_and_country = input_string
    else:
        # Otherwise, the last three parts are joined to form the main_string
        city_and_country = ', '.join(parts[-3:])
    
    # The full_string is the original string
    full_address = input_string
    
    return city_and_country, full_address


def build_calendar_events():
    print('Building Events')
    calendar_events = []
    try:
        # Fetch the calendar data from the URL
        response = requests.get(calendar_url)

        if response.status_code == 200:
            # Parse the iCalendar data
            ical_text = response.text
            c = Calendar(ical_text)

            for event in c.events:
                event_date = event.begin.date()
                event_end_date = event.end.date()
                city_and_country, full_address = split_into_main_and_full(event.location)
                calendar_events.append({ 'name': event.name,
                                         'address': full_address, 
                                         'city': city_and_country, 
                                         'begin': event.begin.date(), 
                                         'end': event.end.date() })
        calendar_events = sorted(calendar_events, key=lambda x: x['begin'])
    except Exception as e:
        print("An error occurred:", str(e))
    
    return calendar_events

events = build_calendar_events()

def rebuild_events_cache(): 
    global events
    events = build_calendar_events()

def get_events_to_show(date_to_check):
    main_event = None
    upcoming_events = []
    current_date = datetime.now().date()
    date_to_check_main_event_for = current_date
    found_main_event = False

    for event in events:
        if not found_main_event and (event['begin'] <= date_to_check_main_event_for and date_to_check_main_event_for <= event['end']):
            main_event = {
                'name': event['name'],
                'address': event['address'],
                'city': event['city'],
                'begin': date_to_check_main_event_for.strftime('%B %d, %Y'),
                'is_future': False
            }
            found_main_event = True
        elif not found_main_event and (date_to_check_main_event_for > event['begin'] and date_to_check_main_event_for > event['end']):
            main_event = {
                'name': event['name'],
                'address': event['address'],
                'city': event['city'],
                'begin': event['begin'].strftime('%B %d %Y'),
                'is_future': True
            }
            found_main_event = True
        elif found_main_event and len(upcoming_events) < 3:
            upcoming_events.append({
                'name': event['name'],
                'address': event['address'],
                'city': event['city'],
                'begin': event['begin'].strftime('%B %d, %Y')
            })
    return { 'main_event': main_event, 'upcoming_events': upcoming_events }

def fetch_data():
    rebuild_events_cache()
    print("Built Cache at", datetime.now())
    # Simulate data fetching
    global last_fetch_time
    last_fetch_time = datetime.now()

@app.before_request
def before_request():
    global last_fetch_time
    with fetch_lock:
        # Check if we need to fetch new data
        if last_fetch_time is None or (datetime.now() - last_fetch_time) > timedelta(minutes=30):
            fetch_data()
            print("Rebuilt the cache...")


@app.route('/')
def index():
    events_data = get_events_to_show(None)
    return render_template('refreshed-main.html', events_data=events_data)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=81, debug=True)
