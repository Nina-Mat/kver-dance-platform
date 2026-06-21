"""Утилиты для построения monthly-view календаря мероприятий."""

import calendar
from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

MONTH_NAMES_RU = [
    '',
    'Январь',
    'Февраль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь',
]

WEEKDAY_NAMES_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']


def shift_month(year, month, delta):
    """Смещает месяц на delta относительно указанной даты."""
    shifted = date(year, month, 1) + relativedelta(months=delta)
    return shifted.year, shifted.month


def get_three_months(center_year, center_month):
    """Возвращает кортежи (год, месяц) для предыдущего, текущего и следующего месяца."""
    prev_year, prev_month = shift_month(center_year, center_month, -1)
    next_year, next_month = shift_month(center_year, center_month, 1)
    return [
        (prev_year, prev_month),
        (center_year, center_month),
        (next_year, next_month),
    ]


def group_events_by_date(events):
    """Группирует мероприятия по дате проведения (без времени)."""
    grouped = defaultdict(list)
    for event in events:
        grouped[event.event_date.date()].append(event)
    return grouped


def build_month_data(year, month, events_by_date):
    """Формирует структуру одного месяца для шаблона календаря."""
    cal = calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        days = []
        for day in week:
            days.append({
                'date': day,
                'in_month': day.month == month,
                'events': events_by_date.get(day, []),
                'is_today': day == date.today(),
            })
        weeks.append(days)

    return {
        'year': year,
        'month': month,
        'month_name': MONTH_NAMES_RU[month],
        'weeks': weeks,
    }


def parse_month_param(month_param):
    """Парсит GET-параметр month=YYYY-MM, возвращает (year, month) или текущий месяц."""
    today = date.today()
    if not month_param:
        return today.year, today.month

    try:
        year_str, month_str = month_param.split('-')
        year, month = int(year_str), int(month_str)
        if 1 <= month <= 12:
            return year, month
    except (ValueError, AttributeError):
        pass

    return today.year, today.month
