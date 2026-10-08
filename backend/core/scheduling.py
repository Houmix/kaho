from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

from .models import Availability, Slot, Unavailability, User


@dataclass(frozen=True)
class Window:
    instructor: User
    start: datetime
    end: datetime


def _aware(d: date, t: time) -> datetime:
    return timezone.make_aware(datetime.combine(d, t))


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def busy_periods(instructor: User, day: date):
    """Créneaux déjà pris ce jour-là : réservations + absences."""
    day_start, day_end = _aware(day, time.min), _aware(day, time.max)
    periods = [
        (_aware(day, s.start_time), _aware(day, s.end_time))
        for s in Slot.objects.filter(instructor=instructor, date=day).exclude(status='CANCELLED')
    ]
    for u in Unavailability.objects.filter(instructor=instructor, start__lt=day_end, end__gt=day_start):
        periods.append((max(u.start, day_start), min(u.end, day_end)))
    return periods


def free_windows(instructor: User, day: date, duration_minutes: int = 60, step_minutes: int = 60):
    """Créneaux proposables = disponibilités récurrentes − absences − réservations, avec préavis minimal."""
    duration, step = timedelta(minutes=duration_minutes), timedelta(minutes=step_minutes)
    earliest = timezone.now() + timedelta(hours=settings.BOOKING_MIN_NOTICE_HOURS)
    busy = busy_periods(instructor, day)
    windows = []
    for a in Availability.objects.filter(instructor=instructor, weekday=day.weekday()):
        cursor, end = _aware(day, a.start_time), _aware(day, a.end_time)
        while cursor + duration <= end:
            w_end = cursor + duration
            if cursor >= earliest and not any(_overlaps(cursor, w_end, b0, b1) for b0, b1 in busy):
                windows.append(Window(instructor, cursor, w_end))
            cursor += step
    return windows


def is_window_free(instructor: User, day: date, start: time, end: time) -> bool:
    w_start, w_end = _aware(day, start), _aware(day, end)
    if w_start < timezone.now() + timedelta(hours=settings.BOOKING_MIN_NOTICE_HOURS):
        return False
    covered = Availability.objects.filter(
        instructor=instructor, weekday=day.weekday(), start_time__lte=start, end_time__gte=end
    ).exists()
    if not covered:
        return False
    return not any(_overlaps(w_start, w_end, b0, b1) for b0, b1 in busy_periods(instructor, day))
