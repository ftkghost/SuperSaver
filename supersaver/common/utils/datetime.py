from datetime import tzinfo, timedelta, datetime
from dateutil.zoneinfo import getzoneinfofile_stream, ZoneInfoFile


class GeneralTZ(tzinfo):
    """
    General timezone with hour offset.
    """
    def __init__(self, hour_offset):
        self.hour_offset = hour_offset

    def __repr__(self):
        return "<TZ{0}>".format(self.hour_offset)

    def utcoffset(self, dt):
        return timedelta(hours=self.hour_offset)

    def tzname(self, dt):
        return "TZ{0}".format(self.hour_offset)

    def dst(self, dt):
        return timedelta(hours=self.hour_offset)


class UTC(tzinfo):
    """
    UTC implementation taken from Python's docs.

    Used only when pytz isn't available.
    """

    def __repr__(self):
        return "<UTC>"

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


EPOCH_TIME = datetime.utcfromtimestamp(0).replace(tzinfo=UTC())


def get_timezone_by_name(tzname):
    zone_info_file = ZoneInfoFile(getzoneinfofile_stream())
    return zone_info_file.zones.get(tzname)


def get_total_seconds_since(date_time=datetime.utcnow().replace(tzinfo=UTC()), since=EPOCH_TIME):
    delta = date_time - since
    return delta.total_seconds()


def to_client_support_time_str(time_value):
    return time_value.replace(microsecond=0).isoformat()


def to_client_timestamp(date_time):
    if not isinstance(date_time, datetime):
        raise TypeError("Argument type should be datetime or date.")
    if date_time is None:
        return None
    if date_time.tzinfo is None:
        time_value = date_time.replace(tzinfo=UTC())
    else:
        time_value = date_time
    delta = (time_value - EPOCH_TIME)
    return int(delta.total_seconds() * 1000)


def from_client_timestamp(timestamp):
    """
    Convert timestamp from client to UTC datetime.
    :param timestamp: timestamp from clients.
    :return: UTC datetime.
    """
    if isinstance(timestamp, str):
        timestamp = int(timestamp)
    timestamp = float(timestamp / 1000.0)
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=UTC())


def from_utc_timestamp(timestamp):
    utc_time = datetime.utcfromtimestamp(timestamp)
    return utc_time.replace(tzinfo=UTC())


def beginning_of_today():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_today():
    return datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)


def beginning_of_week():
    beginning_of_today_time = beginning_of_today()
    day_of_week = beginning_of_today_time.weekday()
    beginning_of_week_time = beginning_of_today_time - timedelta(days=day_of_week)
    return beginning_of_week_time


def end_of_week():
    return beginning_of_week() + timedelta(days=7, microseconds=-1)


def utc_beginning_of_today(timezone_offset_hours):
    # Make sure year,month,day are same as client time.
    now = datetime.utcnow() + timedelta(hours=timezone_offset_hours)
    utc_0am = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC())
    return utc_0am - timedelta(hours=timezone_offset_hours)


def utc_end_of_today(timezone_offset_hours):
    # Make sure year/month/day are same as client time.
    client_time_now = datetime.utcnow() + timedelta(hours=timezone_offset_hours)
    utc_today_end_time = client_time_now.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=UTC())
    return utc_today_end_time - timedelta(hours=timezone_offset_hours)


def utc_beginning_of_week(timezone_offset_hours):
    beginning_of_today_time = utc_beginning_of_today(timezone_offset_hours)
    client_time = datetime.utcnow() + timedelta(hours=timezone_offset_hours)
    day_of_week = client_time.weekday()
    beginning_of_week_time = beginning_of_today_time - timedelta(days=day_of_week)
    return beginning_of_week_time


def utc_end_of_week(timezone_offset_hours):
    return utc_beginning_of_week(timezone_offset_hours) + timedelta(days=7, microseconds=-1)
