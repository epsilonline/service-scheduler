import datetime
from configuration.period import Period

event_time = datetime.datetime.fromisoformat("2022-05-02T15:59:00Z".replace('Z', '+00:00'))

print(f'original event time is {event_time}')

schedule_period = {'begintime': '09:00', 'endtime': '18:00', 'description': 'Office hours', 'weekdays': {'sun-tue'}, 'name': 'office-hours', 'type': 'period'}

period = Period(name=schedule_period['name'],
                begintime=schedule_period['begintime'],
                endtime=schedule_period['endtime'],
                weekdays=schedule_period['weekdays'])

print(period._weekdays_as_numbered_set(schedule_period['weekdays']))

is_in_period = period.time_is_in_period(event_time, 'Europe/Rome')

print(is_in_period)
