from flask import Flask, jsonify, render_template
import requests
from ics import Calendar
from datetime import datetime

app = Flask(__name__)

# Replace the URL with the calendar URL you provided
calendar_url = "https://www.srisriravishankar.org/?post_type=tribe_events&ical=1&eventDisplay=list"

def get_current_or_latest_past_event_location(calendar_url):
    try:
        # Fetch the calendar data from the URL
        response = requests.get(calendar_url)

        if response.status_code == 200:
            # Parse the iCalendar data
            ical_text = response.text
            c = Calendar(ical_text)

            # Get the current date
            current_date = datetime.now().date()

            current_event = None
            current_location = None
            current_event_date = None

            # Iterate through events to find the current day's event or the latest past event
            # print(c)

            closest_future_event = None
            closest_future_date_diff = None
            future_event_flag = False

            for event in c.events:
                print('in an event', event)
                print('in an event.begin', event.begin.date())
                print('in an event.end', event.end.date())
                print('in an event.check', current_date > event.begin.date())
                event_date = event.begin.date()
                event_end_date = event.end.date()
                if event_date == current_date or (event_date <= current_date and current_date <= event_end_date):
                    current_event = event.name
                    current_location = event.location
                    current_event_date = current_date
                    future_event_flag = False
                    print('Found date within event')
                    break  # Stop after finding the first event for the current day
                elif event_date > current_date:
                    date_diff = (event_date - current_date).days
                    if closest_future_event is None or date_diff < closest_future_date_diff:
                        closest_future_event = event
                        closest_future_date_diff = date_diff
                        future_event_flag = True
                        print('Found closer future event')

            # If a current event within or spanning the current date wasn't found, but a future event was:
            if closest_future_event and current_event is None:
                current_event = closest_future_event.name
                current_location = closest_future_event.location
                current_event_date = closest_future_event.begin.date()
            return current_event, current_location, current_event_date, future_event_flag

    except Exception as e:
        print("An error occurred:", str(e))

    return None, None, None

def split_into_main_and_full(input_string):
    # Split the string into parts, trying to split into three parts from the right
    parts = input_string.rsplit(',', 3)
    
    # If there are less than three parts, then the whole input string is the main_string
    if len(parts) <= 3:
        main_string = input_string
    else:
        # Otherwise, the last three parts are joined to form the main_string
        main_string = ', '.join(parts[-3:])
    
    # The full_string is the original string
    full_string = input_string
    
    return main_string, full_string

@app.route('/')
def index():
    current_event, current_location, current_event_date, future_event_flag = get_current_or_latest_past_event_location(calendar_url)
    main_string, full_string = split_into_main_and_full(current_location)
    return render_template('refreshed-main.html', current_event=current_event, current_location=current_location, current_event_date=current_event_date, location=main_string, full_location=full_string, future_event_flag=future_event_flag)

@app.route('/api/event_info')
def api_event_info():
    current_event, current_location, current_event_date = get_current_or_latest_past_event_location(calendar_url)
    response_data = {
        'event': current_event,
        'location': current_location,
        'event_date': str(current_event_date) if current_event_date else None
    }
    return jsonify(response_data)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=80)
