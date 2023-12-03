from datetime import datetime
import pytz


class TimeConverter:

    @staticmethod
    def get_timezone_time(timezone: str = "Europe/Kiev") -> datetime:
        tz = pytz.timezone(timezone)
        return datetime.now(tz)

    @staticmethod
    def str_datetime_to_datetime(str_datetime: str) -> datetime:
        if str_datetime:
            try:
                converted_time = datetime.strptime(str_datetime, '%Y-%m-%d')
                return converted_time
            except ValueError:
                return datetime.strptime(str_datetime.split(".")[0], '%Y-%m-%dT%H:%M:%S')
