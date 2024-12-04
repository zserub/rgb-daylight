from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo  # Built-in in Python 3.9+
from astral import Observer
from astral.sun import sun  # Correct import from astral.sun
from astral import LocationInfo
from rgb import RGB
from pprint import pprint


class Daylight(object):

    def __init__(self, config, rgb):
        self.config = config
        self.lights = rgb
        self._position = None
        self.position = self.config.get("position", {"timezone": "Europe/Budapest", "latitude": 47.4979, "longitude": 19.0402})
        self._sun = None
        self.timezone_hours = self.config.get("timezone_offset", 0)
        self.colors_default = {
                "night-end": [0, 0, 0.05],
                "dawn": [0.1, 0.1, 0.3],
                "sunrise": [0.4, 0.4, 0.4],
                "noon": [1, 1, 1],
                "sunset": [0.5, 0.25, 0.1],
                "dusk": [0.3, 0.1, 0.4],
                "night-start": [0, 0, 0.05]
        }
        self.colors = self.config.get("colors", self.colors_default)
        self.time_of_day = ['night-start', "dusk", "sunset", "noon", "sunrise", "dawn", 'night-end']
        self.start = self.tz_fix(datetime.now()).replace(tzinfo=ZoneInfo("UTC"))
        self.test = False

    def set_color(self, color):
        self.lights.color = self.colors[color]

    def update(self):
        current_time = self.now()
        # print(f"Time: {current_time}")
        # pprint(self.f_sun)

        # Handle night wrap around with normalized times
        night_start = self.f_sun['night-start']
        night_end = self.f_sun['night-end']

        if night_start <= current_time or current_time < night_end:
            self.lights.color = self.smooth("night-start", "night-end")
            return

        # Determine appropriate time of day block
        for i, time_key in enumerate(self.time_of_day):
            next_time_key = self.time_of_day[(i + 1) % len(self.time_of_day)]  # Handle wraparound
            start_time = self.f_sun[time_key]
            end_time = self.f_sun[next_time_key]

            # Handle day transitions where end_time is earlier than start_time (spans midnight)
            # if end_time < start_time:
            #     end_time += timedelta(days=1)  # Add a day to end_time

            # current_utc = current_time.astimezone(timezone.utc)  # Ensure current_time is UTC
            # if start_time <= current_utc < end_time:  # Check if current_time falls within this range
            #     print(f"Debug: Active block detected - {time_key} to {next_time_key}")
            #     self.lights.color = self.smooth(time_key, next_time_key)
            #     break


    def smooth(self, start, end):
        if start not in self.colors or end not in self.colors:
            print(f"Error: Missing color for {start} or {end}")
            return [0, 0, 0]

        current_time = self.now()
        start_time = self.f_sun[start]
        end_time = self.f_sun[end]

        print(f"Debug: current_time={current_time}, start_time={start_time}, end_time={end_time}")

        ratio = self.calculate_ratio(start_time, end_time, current_time)

        color = [0, 0, 0]
        for key in range(len(self.colors[start])):
            color[key] = self.colors[start][key] * (1 - ratio) + self.colors[end][key] * ratio
            color[key] = max(0, min(1, color[key]))

        print(f"Time: {current_time}")
        print(f"Ratio ({start}/{end}): {ratio:.5f}")
        print(f"R={color[0]:.2f}, G={color[1]:.2f}, B={color[2]:.2f}\n")
        return color

    def calculate_ratio(self, start_time, end_time, current_time):
        # Convert all times to UTC
        start_utc = start_time.astimezone(timezone.utc)
        end_utc = end_time.astimezone(timezone.utc)
        current_utc = current_time.astimezone(timezone.utc)

        # Convert to seconds since midnight UTC
        start_seconds = self.time_to_seconds(start_utc)
        end_seconds = self.time_to_seconds(end_utc)
        current_seconds = self.time_to_seconds(current_utc)

        print(f"Debug: start_seconds={start_seconds}, end_seconds={end_seconds}, current_seconds={current_seconds}")

        # Handle day transition
        if end_seconds < start_seconds:  # Adjust for next-day end time
            end_seconds += 24 * 3600
        if current_seconds < start_seconds:  # Handle current time before start time
            current_seconds += 24 * 3600

        # Recalculate the time difference
        total_seconds = end_seconds - start_seconds
        elapsed_seconds = max(0, min(current_seconds - start_seconds, total_seconds))

        # Handle edge cases
        if total_seconds == 0:
            return 0  # Avoid division by zero
        
        ratio = elapsed_seconds / total_seconds if total_seconds > 0 else 0

        # Ensure ratio is between 0 and 1
        ratio = max(0, min(1, ratio))

        print(f"Debug: total_seconds={total_seconds}, elapsed_seconds={elapsed_seconds}, ratio={ratio}")

        return round(ratio, 5)  # Round to 5 decimal places for consistency with ratio

    def time_to_seconds(self, time):
        """Convert time to total seconds in a 24-hour format"""
        return time.hour * 3600 + time.minute * 60 + time.second

    def now(self):
        if self.test:
            self.start += timedelta(minutes=1)
            return self.start.replace(microsecond=0)  # Strip microseconds for consistency
        else:
            return self.tz_fix(datetime.now()).replace(tzinfo=ZoneInfo("UTC"), microsecond=0)

    def tz_fix(self, utc_time):
        try:
            local_time = utc_time.astimezone(ZoneInfo(self.position["timezone"]))  # Use position's timezone
        except KeyError:
            print(f"Timezone not found in position: {self.position}")
            local_time = utc_time  # Fallback to UTC if timezone is missing
        return local_time

    @property
    def f_sun(self):
        # Use `sun()` to get solar events, which returns all necessary times including dawn and dusk
        s = sun(self.observer, self.now())  # Correct usage of the sun function from astral.sun

        # Ensure times are adjusted to the correct timezone
        for key in s:
            s[key] = self.tz_fix(s[key])  # Adjust times for timezone

        # Manually adjust night-start and night-end
        s['night-start'] = s['dusk'] + timedelta(minutes=1)  # Night starts just after dusk
        s['night-end'] = s['dawn'] - timedelta(minutes=1)  # Night ends just before dawn

        return s

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value  # Fixed the typo here
        city = LocationInfo("", "", value["timezone"], value["latitude"], value["longitude"])
        self.observer = city.observer
