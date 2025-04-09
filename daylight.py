from datetime import datetime, timedelta  # timezone
# from zoneinfo import ZoneInfo  # Built-in in Python 3.9+
from astral import Observer
from astral.sun import sun  # Correct import from astral.sun
from astral import LocationInfo
from rgb import RGB
# from pprint import pprint


class Daylight(object):

    def __init__(self, config, rgb):
        self.config = config
        self.lights = rgb
        self._position = None
        self.position = self.config.get("position", {
                                        "timezone": "Europe/Budapest", "latitude": 47.4979, "longitude": 19.0402})
        self._sun = None
        self.timezone_hours = self.config.get("timezone_offset", 0)
        self.colors_default = {
            "night-end": [0, 0, 0.05],
            "dawn": [0.1, 0.1, 0.3],
            "sunrise": [0.4, 0.4, 0.4],
            "noon": [1, 1, 1],
            "sunset": [0.5, 0.25, 0.1],
            "dusk": [0.3, 0.1, 0.4],
            "night-start": [0, 0, 0.05],
            "midnight": [0, 0, 0.05],
            "new-day": [0, 0, 0.05]
        }
        self.colors = self.config.get("colors", self.colors_default)
        self.time_of_day = ['midnight', 'night-start', "dusk",
                            "sunset", "noon", "sunrise", "dawn", 'night-end', 'new-day']
        # self.start = datetime.now()
        self.test = False

    def set_color(self, color):
        self.lights.color = self.colors[color]

    def update(self, current_time):
        # print(datetime.now())
        print(f'Current time: {current_time}')
        # s = sun(self.observer, datetime.today())
        s = dict.fromkeys(self.time_of_day, 0)

        # Manually adjust night-start and night-end
        s["dawn"] = datetime.now().replace(hour=6, minute=5, second=0)
        s["dusk"] = datetime.now().replace(hour=20, minute=0, second=0)
        s["sunrise"] = datetime.now().replace(hour=6, minute=0, second=0)
        s["noon"] = datetime.now().replace(hour=12, minute=0, second=0)
        s["sunset"] = datetime.now().replace(hour=19, minute=0, second=0)

        # Night starts just after dusk
        s['night-start'] = s['dusk'] + timedelta(minutes=60)
        # Night ends just before dawn
        s['night-end'] = s['dawn'] - timedelta(minutes=60)
        print(s['night-start'], '\t', s['night-end'])
        s["midnight"] = datetime.now().replace(hour=23, minute=59, second=59)
        s["new-day"] = datetime.now().replace(hour=0, minute=0, second=0)

        start_sec, end_sec, start_time, end_time = self.get_current_timeOfDay(
            s, current_time)
        # print(f"DEBUG:Start time: {start_sec}, End time: {end_sec}")
        self.lights.color = self.transition(
            start_sec, end_sec, current_time, self.colors[start_time], self.colors[end_time])

    def transition(self, start_time, stop_time, current_time, start_values, end_values):
        total_duration = stop_time-start_time
        elapsed_duration = current_time - start_time
        ratio = elapsed_duration / total_duration
        color = [0, 0, 0]
        for i in range(0, 3):
            color[i] = round(
                (start_values[i] + (end_values[i] - start_values[i]) * ratio), 3)
        # print(color)
        return color

    def get_current_timeOfDay(self, times_of_day, current_time):
        ToD_seconds = {}
        for act_key, value in times_of_day.items():
            date = times_of_day[act_key]
            hour = date.hour
            minute = date.minute
            second = date.second
            ToD_seconds[act_key] = hour * 3600 + minute * 60 + second

        if current_time == 86399:  # 23:59:59 daywrap
            above = 'new-day'
        else:
            above = min((k for k, v in ToD_seconds.items() if v > current_time),
                        key=lambda k: abs(ToD_seconds[k] - current_time), default=None)
        below = min((k for k, v in ToD_seconds.items() if v <= current_time),
                    key=lambda k: abs(ToD_seconds[k] - current_time), default=None)

        print(f"Closest below: {below}, Closest above: {above}")

        start_time = ToD_seconds[below]
        end_time = ToD_seconds[above]
        return start_time, end_time, below, above

    def time_to_seconds(self, time):
        """Convert time to total seconds in a 24-hour format"""
        return time.hour * 3600 + time.minute * 60 + time.second

    # def now(self):
    #     if self.test:
    #         self.start += timedelta(minutes=1)
    #         return self.start.replace(microsecond=0)  # Strip microseconds for consistency
    #     else:
    #         return self.tz_fix(datetime.now()).replace(tzinfo=ZoneInfo("UTC"), microsecond=0)

    # def tz_fix(self, utc_time):
    #     try:
    #         local_time = utc_time.astimezone(ZoneInfo(self.position["timezone"]))  # Use position's timezone
    #     except KeyError:
    #         print(f"Timezone not found in position: {self.position}")
    #         local_time = utc_time  # Fallback to UTC if timezone is missing
    #     return local_time

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        city = LocationInfo(
            "", "", value["timezone"], value["latitude"], value["longitude"])
        self.observer = city.observer
