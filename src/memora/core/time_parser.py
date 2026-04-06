"""Natural language time parsing for Memora v3.1.

Converts natural language time expressions to date ranges for temporal queries.
Examples: "last week", "yesterday", "this month", "2 days ago", etc.
"""

import re
from datetime import datetime, timedelta, date
from typing import Tuple, Optional
from dateutil import parser as date_parser


class TimeQueryParser:
    """Parse natural language time expressions into date ranges."""

    def __init__(self):
        # Precompiled regex patterns for common time expressions
        self.patterns = [
            # Relative time patterns
            (r"\b(?:today|now)\b", self._parse_today),
            (r"\byesterday\b", self._parse_yesterday),
            (r"\btomorrow\b", self._parse_tomorrow),
            # Last/this/next patterns
            (r"\blast\s+(week|month|year|hour|day)\b", self._parse_last_period),
            (r"\bthis\s+(week|month|year|hour|day)\b", self._parse_this_period),
            (r"\bnext\s+(week|month|year|hour|day)\b", self._parse_next_period),
            # Numeric relative patterns
            (
                r"\b(\d+)\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\s+ago\b",
                self._parse_ago,
            ),
            (
                r"\bin\s+(\d+)\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b",
                self._parse_in_future,
            ),
            # Recent/older patterns
            (r"\brecent(?:ly)?\b", self._parse_recently),
            (r"\bold(?:er)?\b", self._parse_older),
            # Date ranges
            (r"\bbetween\s+(.+?)\s+and\s+(.+)", self._parse_between),
            (r"\bsince\s+(.+)", self._parse_since),
            (r"\bbefore\s+(.+)", self._parse_before),
            (r"\bafter\s+(.+)", self._parse_after),
            # Specific date patterns
            (r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", self._parse_date),
            (r"\b(\d{4}-\d{2}-\d{2})\b", self._parse_iso_date),
        ]

    def parse_time_query(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse natural language time query into date range.

        Returns:
            Tuple of (start_date, end_date) or None if no time expression found
        """
        query_lower = query.lower().strip()

        # Try each pattern
        for pattern, handler in self.patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                try:
                    result = handler(match)
                    if result:
                        return result
                except Exception:
                    continue  # Try next pattern

        # Try to parse as a general date if no patterns matched
        try:
            parsed_date = date_parser.parse(query, fuzzy=True)
            # Return single day range
            start = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        except Exception:
            pass

        return None

    def _parse_today(self, match) -> Tuple[datetime, datetime]:
        """Parse 'today' or 'now'."""
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def _parse_yesterday(self, match) -> Tuple[datetime, datetime]:
        """Parse 'yesterday'."""
        yesterday = datetime.now() - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def _parse_tomorrow(self, match) -> Tuple[datetime, datetime]:
        """Parse 'tomorrow'."""
        tomorrow = datetime.now() + timedelta(days=1)
        start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def _parse_last_period(self, match) -> Tuple[datetime, datetime]:
        """Parse 'last week/month/year/day'."""
        period = match.group(1)
        now = datetime.now()

        if period == "day":
            return self._parse_yesterday(match)
        elif period == "week":
            # Last week (Monday to Sunday)
            days_since_monday = now.weekday()
            last_monday = now - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = last_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "month":
            # Last month
            if now.month == 1:
                last_month = now.replace(year=now.year - 1, month=12, day=1)
            else:
                last_month = now.replace(month=now.month - 1, day=1)

            # Last day of last month
            if last_month.month == 12:
                next_month = last_month.replace(year=last_month.year + 1, month=1, day=1)
            else:
                next_month = last_month.replace(month=last_month.month + 1, day=1)

            last_day = next_month - timedelta(days=1)

            start = last_month.replace(hour=0, minute=0, second=0, microsecond=0)
            end = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "year":
            # Last year
            last_year = now.replace(year=now.year - 1, month=1, day=1)
            last_year_end = now.replace(year=now.year - 1, month=12, day=31)
            start = last_year.replace(hour=0, minute=0, second=0, microsecond=0)
            end = last_year_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "hour":
            # Last hour
            last_hour = now - timedelta(hours=1)
            start = last_hour.replace(minute=0, second=0, microsecond=0)
            end = last_hour.replace(minute=59, second=59, microsecond=999999)
            return start, end

        return None

    def _parse_this_period(self, match) -> Tuple[datetime, datetime]:
        """Parse 'this week/month/year/day'."""
        period = match.group(1)
        now = datetime.now()

        if period == "day":
            return self._parse_today(match)
        elif period == "week":
            # This week (Monday to Sunday)
            days_since_monday = now.weekday()
            this_monday = now - timedelta(days=days_since_monday)
            this_sunday = this_monday + timedelta(days=6)
            start = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = this_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "month":
            # This month
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of this month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            last_day = next_month - timedelta(days=1)
            end = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "year":
            # This year
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "hour":
            # This hour
            start = now.replace(minute=0, second=0, microsecond=0)
            end = now.replace(minute=59, second=59, microsecond=999999)
            return start, end

        return None

    def _parse_next_period(self, match) -> Tuple[datetime, datetime]:
        """Parse 'next week/month/year/day'."""
        period = match.group(1)
        now = datetime.now()

        if period == "day":
            return self._parse_tomorrow(match)
        elif period == "week":
            # Next week (Monday to Sunday)
            days_since_monday = now.weekday()
            next_monday = now + timedelta(days=7 - days_since_monday)
            next_sunday = next_monday + timedelta(days=6)
            start = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = next_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "month":
            # Next month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)

            # Last day of next month
            if next_month.month == 12:
                following_month = next_month.replace(year=next_month.year + 1, month=1, day=1)
            else:
                following_month = next_month.replace(month=next_month.month + 1, day=1)

            last_day = following_month - timedelta(days=1)

            start = next_month.replace(hour=0, minute=0, second=0, microsecond=0)
            end = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        elif period == "year":
            # Next year
            next_year = now.replace(year=now.year + 1, month=1, day=1)
            next_year_end = now.replace(year=now.year + 1, month=12, day=31)
            start = next_year.replace(hour=0, minute=0, second=0, microsecond=0)
            end = next_year_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end

        return None

    def _parse_ago(self, match) -> Tuple[datetime, datetime]:
        """Parse 'X days/weeks/months ago'."""
        amount = int(match.group(1))
        unit = match.group(2).rstrip("s")  # Remove plural 's'
        now = datetime.now()

        if unit in ["second", "seconds"]:
            target = now - timedelta(seconds=amount)
        elif unit in ["minute", "minutes"]:
            target = now - timedelta(minutes=amount)
        elif unit in ["hour", "hours"]:
            target = now - timedelta(hours=amount)
        elif unit in ["day", "days"]:
            target = now - timedelta(days=amount)
        elif unit in ["week", "weeks"]:
            target = now - timedelta(weeks=amount)
        elif unit in ["month", "months"]:
            target = now - timedelta(days=amount * 30)  # Approximate
        elif unit in ["year", "years"]:
            target = now - timedelta(days=amount * 365)  # Approximate
        else:
            return None

        # Return range around that time (same day)
        start = target.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def _parse_in_future(self, match) -> Tuple[datetime, datetime]:
        """Parse 'in X days/weeks/months'."""
        amount = int(match.group(1))
        unit = match.group(2).rstrip("s")  # Remove plural 's'
        now = datetime.now()

        if unit in ["second", "seconds"]:
            target = now + timedelta(seconds=amount)
        elif unit in ["minute", "minutes"]:
            target = now + timedelta(minutes=amount)
        elif unit in ["hour", "hours"]:
            target = now + timedelta(hours=amount)
        elif unit in ["day", "days"]:
            target = now + timedelta(days=amount)
        elif unit in ["week", "weeks"]:
            target = now + timedelta(weeks=amount)
        elif unit in ["month", "months"]:
            target = now + timedelta(days=amount * 30)  # Approximate
        elif unit in ["year", "years"]:
            target = now + timedelta(days=amount * 365)  # Approximate
        else:
            return None

        # Return range around that time (same day)
        start = target.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def _parse_recently(self, match) -> Tuple[datetime, datetime]:
        """Parse 'recently' (last 7 days)."""
        now = datetime.now()
        start = now - timedelta(days=7)
        return start, now

    def _parse_older(self, match) -> Tuple[datetime, datetime]:
        """Parse 'older' (more than 30 days ago)."""
        now = datetime.now()
        end = now - timedelta(days=30)
        start = datetime.min  # Beginning of time
        return start, end

    def _parse_between(self, match) -> Tuple[datetime, datetime]:
        """Parse 'between X and Y'."""
        try:
            start_str = match.group(1).strip()
            end_str = match.group(2).strip()

            start = date_parser.parse(start_str, fuzzy=True)
            end = date_parser.parse(end_str, fuzzy=True)

            return start, end
        except Exception:
            return None

    def _parse_since(self, match) -> Tuple[datetime, datetime]:
        """Parse 'since X'."""
        try:
            date_str = match.group(1).strip()
            start = date_parser.parse(date_str, fuzzy=True)
            end = datetime.now()
            return start, end
        except Exception:
            return None

    def _parse_before(self, match) -> Tuple[datetime, datetime]:
        """Parse 'before X'."""
        try:
            date_str = match.group(1).strip()
            end = date_parser.parse(date_str, fuzzy=True)
            start = datetime.min  # Beginning of time
            return start, end
        except Exception:
            return None

    def _parse_after(self, match) -> Tuple[datetime, datetime]:
        """Parse 'after X'."""
        try:
            date_str = match.group(1).strip()
            start = date_parser.parse(date_str, fuzzy=True)
            end = datetime.now()
            return start, end
        except Exception:
            return None

    def _parse_date(self, match) -> Tuple[datetime, datetime]:
        """Parse specific date format."""
        try:
            date_str = match.group(1)
            parsed_date = date_parser.parse(date_str)
            start = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        except Exception:
            return None

    def _parse_iso_date(self, match) -> Tuple[datetime, datetime]:
        """Parse ISO date format (YYYY-MM-DD)."""
        try:
            date_str = match.group(1)
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            start = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        except Exception:
            return None


def parse_time_query(query: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Parse natural language time query into date range.

    Examples:
        "last week" -> (Monday of last week, Sunday of last week)
        "yesterday" -> (yesterday 00:00, yesterday 23:59)
        "2 days ago" -> (2 days ago 00:00, 2 days ago 23:59)
        "since monday" -> (last Monday 00:00, now)
        "before 2024-01-01" -> (beginning of time, 2024-01-01 00:00)

    Args:
        query: Natural language time expression

    Returns:
        Tuple of (start_datetime, end_datetime) or None if no time found
    """
    parser = TimeQueryParser()
    return parser.parse_time_query(query)


# Example usage and testing
if __name__ == "__main__":
    test_queries = [
        "last week",
        "yesterday",
        "today",
        "this month",
        "2 days ago",
        "in 3 hours",
        "recently",
        "since monday",
        "between 2024-01-01 and 2024-01-31",
        "before christmas",
        "after 2023-12-01",
        "2024-03-15",
        "older memories",
    ]

    parser = TimeQueryParser()
    for query in test_queries:
        result = parser.parse_time_query(query)
        if result:
            start, end = result
            print(
                f"'{query}' -> {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            print(f"'{query}' -> No time expression found")
