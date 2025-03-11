import datetime
import pytz
from utils.logger import get_logger

logger = get_logger('Period')

weekdays_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


class Period:
    def __init__(self, name, begintime: str = None, endtime: str = None, weekdays: set = None):

        """
        Defines a period in which an instance should be running
        :param name: name of the period
        :param begintime: begin time of the period (time)
        :param endtime: end time of the period (time)
        :param weekdays: weekdays (set 0..6)
        :param months: months of the period (set 1..12)
        :param monthdays: days in the month (set 1..28-31)
        """
        self.name = name
        self.begintime = datetime.time.fromisoformat(begintime)
        self.endtime = datetime.time.fromisoformat(endtime)
        self.weekdays = self._weekdays_as_numbered_set(weekdays)

        logger.debug(f'period-name: {self.name}, begintime: {self.begintime}, endtime: {self.endtime}, weekdays: {self.weekdays}')

    @staticmethod
    def _weekdays_as_numbered_set(weekdays_as_string:set) -> set:

        numbered_set = set()

        if weekdays_as_string is None:
            return {0, 1, 2, 3, 4, 5, 6}

        for weekdays_element in weekdays_as_string:

            weekdays_splitted = weekdays_element.split('-') if '-' in weekdays_element else weekdays_element.split(',')

            if len(weekdays_splitted) == 1:
                numbered_set.add(weekdays_names.index(weekdays_splitted[0]))

            elif len(weekdays_splitted) == 2:
                start_day_idx = weekdays_names.index(weekdays_splitted[0])
                end_day_idx = weekdays_names.index(weekdays_splitted[1])

                if start_day_idx <= end_day_idx:
                    numbered_set.update(range(start_day_idx, end_day_idx+1))
                else:
                    numbered_set.update(range(start_day_idx, len(weekdays_names)))
                    numbered_set.update(range(0, end_day_idx+1))
            elif 2 < len(weekdays_splitted) <= 7:
                for day in weekdays_splitted:
                    numbered_set.add(weekdays_names.index(day))
            else:
                raise Exception("Invalid scheduler weekdays range")

        return numbered_set

    def time_is_in_period(self, time: datetime.datetime, timezone_name: str) -> bool:

        result = False

        time_timezoned = time.astimezone(pytz.timezone(timezone_name))
        logger.debug(f'Timezoned event is: {time_timezoned}')
        event_weekday = time_timezoned.weekday()
        logger.debug(f'Event weekday {event_weekday}')

        if event_weekday in self.weekdays:
            logger.debug(f'event is in weekdays')
            event_hour = time_timezoned.time()
            logger.debug(f'event hour is {event_hour}')

            if self.begintime <= event_hour <= self.endtime:
                result = True
                logger.debug(f'event is in period')

        return result
