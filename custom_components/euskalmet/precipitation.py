"""Precipitation accumulation for the Euskalmet integration.

Pure helpers without Home Assistant dependencies, so they can be tested alone.

How Euskalmet publishes precipitation (checked against the live API):

* The hourly endpoint ``readings/forStation/{station}/{sensor}/measures/
  {measureType}/{measure}/at/{YYYY}/{MM}/{DD}/{HH}`` takes the hour in UTC and
  returns six 10-minute slots. Their labels (``slots[].lowerEndPointDesc``,
  e.g. "17:20") are UTC as well, although the API calls them "LocalTime".
* Each label is the END of the 10-minute interval it measures: the value
  labelled 20:20 is the rain between 20:10 and 20:20, published some minutes
  later (observed: 20:20 UTC already available at 20:24 UTC). The API describes
  the slot as [20:20..20:29:59.999], but that is only the bucket holding the
  timestamp.
* Euskalmet assigns to a local date the slots labelled 00:00 to 23:50 local
  time, and its official daily totals are the sum of those slots. The
  ``summarized/byDay`` endpoint sums the UTC day instead, so it is not used.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Collection, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone, tzinfo
import math
from typing import Any

# Downloads the slots of a UTC hour: readings by slot time, an empty mapping
# when the hour has no data (HTTP 404) or None when the request failed.
HourFetcher = Callable[[datetime], Awaitable[Mapping[datetime, float | None] | None]]

SLOT_LENGTH = timedelta(minutes=10)
SLOTS_PER_HOUR = 6

# Right after midnight the previous day is still reported until its total has
# been published with its last slot (23:50); this is the safety limit.
DAY_ROLLOVER_DEADLINE = time(1, 0)

# Euskalmet publishes a slot every 10 minutes even when it does not rain (0.0),
# so when the latest slot is older than this the API or the gauge is failing
# and nothing is reported.
MAX_READING_AGE = timedelta(hours=1)

# Incomplete hours (late data after an outage) are downloaded again at most once
# per RECHECK_INTERVAL, while they ended less than RECHECK_WINDOW ago.
RECHECK_INTERVAL = timedelta(hours=1)
RECHECK_WINDOW = timedelta(hours=6)


@dataclass(frozen=True)
class Reading:
    """A 10-minute reading; ``time`` is the Euskalmet label (end of the interval)."""

    time: datetime
    value: float


@dataclass(frozen=True)
class DayTotal:
    """Accumulated precipitation of a local day."""

    day: date
    total: float
    readings_count: int
    last_reading_time: datetime | None


@dataclass(frozen=True)
class WindowTotal:
    """Accumulated precipitation of a period ending at the latest slot."""

    total: float
    readings_count: int
    start: datetime
    end: datetime


@dataclass(frozen=True)
class PrecipitationSnapshot:
    """Values to publish after a poll; None means unavailable."""

    latest: Reading | None = None
    last_hour: WindowTotal | None = None
    today: DayTotal | None = None
    # Local midnight of the reported day (last_reset of the daily total)
    today_reset: datetime | None = None


def to_float(value: Any) -> float | None:
    """Return a reading as float, or None when it is null or not a valid amount."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def floor_to_hour(moment: datetime) -> datetime:
    """Return the start of the UTC hour containing an aware datetime."""
    return moment.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def parse_hour(data: Mapping[str, Any], hour: datetime) -> dict[datetime, float | None]:
    """Map the slots of an hourly response to their UTC label times.

    ``hour`` is the UTC hour requested in the URL. Unpublished or invalid
    values are returned as None.
    """
    hour = floor_to_hour(hour)
    slots = data.get("slots") or []
    values = data.get("values") or []
    readings: dict[datetime, float | None] = {}
    for index, value in enumerate(values):
        slot = slots[index] if index < len(slots) else None
        readings[_slot_time(slot, hour, index)] = to_float(value)
    return readings


def _slot_time(slot: Any, hour: datetime, index: int) -> datetime:
    """Return the UTC label time of a slot, falling back to its position."""
    label = slot.get("lowerEndPointDesc") if isinstance(slot, Mapping) else None
    try:
        hours, minutes = (int(part) for part in str(label).split(":"))
        return hour.replace(hour=hours, minute=minutes)
    except ValueError:
        return hour + index * SLOT_LENGTH


def local_day_range(day: date, tz: tzinfo) -> tuple[datetime, datetime]:
    """Return the UTC [start, end) range of the slot labels of a local day."""
    start = datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz).astimezone(
        timezone.utc
    )
    return start, end


def local_day_hours(day: date, tz: tzinfo) -> list[datetime]:
    """Return the UTC hours to download for a local day (23, 24 or 25 in Spain)."""
    start, end = local_day_range(day, tz)
    hours = []
    hour = floor_to_hour(start)
    while hour < end:
        hours.append(hour)
        hour += timedelta(hours=1)
    return hours


def last_slot_of_day(day: date, tz: tzinfo) -> datetime:
    """Return the UTC label time of the last slot of a local day (23:50)."""
    return local_day_range(day, tz)[1] - SLOT_LENGTH


def day_total(readings: Mapping[datetime, float], day: date, tz: tzinfo) -> DayTotal:
    """Sum the readings Euskalmet assigns to a local day (00:00 to 23:50)."""
    start, end = local_day_range(day, tz)
    slots = sorted(slot for slot in readings if start <= slot < end)
    return DayTotal(
        day=day,
        total=_sum(readings[slot] for slot in slots),
        readings_count=len(slots),
        last_reading_time=slots[-1] if slots else None,
    )


def last_hour_total(readings: Mapping[datetime, float]) -> WindowTotal | None:
    """Sum the six slots of the 60 minutes ending at the latest published slot."""
    if not readings:
        return None
    end = max(readings)
    start = end - SLOTS_PER_HOUR * SLOT_LENGTH
    slots = [slot for slot in readings if start < slot <= end]
    return WindowTotal(
        total=_sum(readings[slot] for slot in slots),
        readings_count=len(slots),
        start=start,
        end=end,
    )


def target_day(now: datetime, tz: tzinfo, reported: DayTotal | None) -> date:
    """Return the local day whose total has to be reported at ``now``.

    After midnight the previous day is kept until its total has been reported
    including its last slot (23:50), so the statistics get the whole day, or
    until DAY_ROLLOVER_DEADLINE. ``reported`` is the last total reported.
    """
    local_now = now.astimezone(tz)
    today = local_now.date()
    yesterday = today - timedelta(days=1)
    if (
        local_now.time() >= DAY_ROLLOVER_DEADLINE
        or (reported is not None and reported.day == today)
        or (
            reported is not None
            and reported.last_reading_time == last_slot_of_day(yesterday, tz)
        )
    ):
        return today
    return yesterday


def _sum(values: Iterable[float]) -> float:
    """Add readings without floating point noise (5.1 + 7.9 + ... = 74.6)."""
    return round(math.fsum(values), 2)


class PrecipitationAccumulator:
    """Readings of one precipitation sensor for the current and previous day.

    Readings are stored by slot time, so downloading an hour again never counts
    a slot twice. Totals are always recomputed from all stored readings.
    """

    def __init__(self) -> None:
        """Initialize an empty accumulator."""
        self.readings: dict[datetime, float] = {}
        # UTC hour -> time of its last successful download
        self._downloaded: dict[datetime, datetime] = {}
        # Last daily total reported
        self._reported: DayTotal | None = None

    async def update(
        self, now: datetime, tz: tzinfo, fetch: HourFetcher, parallel: int = 4
    ) -> PrecipitationSnapshot:
        """Download the hours needed at ``now`` and return the values to publish.

        Every poll downloads the current and previous UTC hours, where new and
        late slots appear, plus the hours of the reported day still missing
        (after a restart or failed polls), ``parallel`` at a time.
        """
        refreshed = self.hours_to_refresh(now)
        await self._download(refreshed, now, fetch, parallel)
        await self._download(
            self.hours_to_backfill(now, tz, skip=refreshed), now, fetch, parallel
        )
        self.prune(now, tz)
        return self.snapshot(now, tz)

    async def _download(
        self,
        hours: Iterable[datetime],
        now: datetime,
        fetch: HourFetcher,
        parallel: int,
    ) -> None:
        """Download several hours and store the successful ones."""
        semaphore = asyncio.Semaphore(parallel)

        async def download(hour: datetime) -> None:
            async with semaphore:
                readings = await fetch(hour)
            if readings is not None:
                self.add_hour(hour, readings, now)

        await asyncio.gather(*(download(hour) for hour in hours))

    def hours_to_refresh(self, now: datetime) -> list[datetime]:
        """Return the hours to download on every poll: new and late slots land there."""
        current = floor_to_hour(now)
        return [current - timedelta(hours=1), current]

    def hours_to_backfill(
        self, now: datetime, tz: tzinfo, skip: Collection[datetime] = ()
    ) -> list[datetime]:
        """Return the hours of the reported day still missing or due for a re-check."""
        current = floor_to_hour(now)
        hours = []
        for hour in local_day_hours(target_day(now, tz, self._reported), tz):
            if hour > current or hour in skip:
                continue
            downloaded = self._downloaded.get(hour)
            if downloaded is None or (
                not self._is_complete(hour)
                and now - (hour + timedelta(hours=1)) < RECHECK_WINDOW
                and now - downloaded >= RECHECK_INTERVAL
            ):
                hours.append(hour)
        return hours

    def add_hour(
        self,
        hour: datetime,
        readings: Mapping[datetime, float | None],
        downloaded_at: datetime,
    ) -> None:
        """Store a successful download (no readings for an hour without data).

        A null value never erases a stored reading: a late or empty response
        must not make the total go down.
        """
        for slot, value in readings.items():
            if value is not None:
                self.readings[slot] = value
        self._downloaded[floor_to_hour(hour)] = downloaded_at

    def prune(self, now: datetime, tz: tzinfo) -> None:
        """Forget everything older than the previous local day."""
        yesterday = now.astimezone(tz).date() - timedelta(days=1)
        start = local_day_range(yesterday, tz)[0]
        self.readings = {
            slot: value for slot, value in self.readings.items() if slot >= start
        }
        self._downloaded = {
            hour: when
            for hour, when in self._downloaded.items()
            if hour >= floor_to_hour(start)
        }

    def snapshot(self, now: datetime, tz: tzinfo) -> PrecipitationSnapshot:
        """Return the values to publish at ``now`` (None when unavailable)."""
        latest = max(self.readings, default=None)
        if latest is None or now - latest > MAX_READING_AGE:
            return PrecipitationSnapshot()
        today = self._today(now, target_day(now, tz, self._reported), tz)
        return PrecipitationSnapshot(
            latest=Reading(latest, self.readings[latest]),
            last_hour=last_hour_total(self.readings),
            today=today,
            today_reset=(
                datetime.combine(today.day, time.min, tzinfo=tz)
                if today is not None
                else None
            ),
        )

    def _today(self, now: datetime, day: date, tz: tzinfo) -> DayTotal | None:
        """Return the total of the reported day, never a value made up by a failure.

        The total is valid when every hour of the day up to the current one has
        been downloaded at least once (an hour without data yet counts). If not,
        e.g. after a restart or a new day while the API fails, the last valid
        total of the same day is kept, if there is one.
        """
        current = floor_to_hour(now)
        if all(
            hour in self._downloaded
            for hour in local_day_hours(day, tz)
            if hour <= current
        ):
            self._reported = day_total(self.readings, day, tz)
            return self._reported
        if self._reported is not None and self._reported.day == day:
            return self._reported
        return None

    def _is_complete(self, hour: datetime) -> bool:
        """Return True when all six slots of an hour have a reading."""
        end = hour + timedelta(hours=1)
        return sum(1 for slot in self.readings if hour <= slot < end) >= SLOTS_PER_HOUR
