import re

from dataclasses import dataclass

from server.exceptions import ArgumentError
@dataclass
class BanTimeUnits:
    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0

class BanDuration:
    TIME_AND_UNIT_RE = re.compile(r'(\d*)(\w*)')
    def __init__(self, ban_duration: str):
        self.ban_duration_arg = ban_duration
        self.ban_duration = BanTimeUnits()

        self._solve_ban_duration_time_unit()
    
    def _solve_ban_duration_time_unit(self):
        search_results = self.TIME_AND_UNIT_RE.search(self.ban_duration_arg)
        duration = 0
        if search_results.group(1) != '':
            duration = int(search_results.group(1))

        if search_results.group(2) != '':
            unit = search_results.group(2).lower()

            if unit.startswith('s'):
                self.ban_duration.seconds = duration
            elif unit.startswith('m'):
                self.ban_duration.minutes = duration
            elif unit.startswith('h'):
                self.ban_duration.hours = duration
            elif unit.startswith('d'):
                self.ban_duration.days = duration
            # P for PermaBan
            elif unit.startswith('p'):
                self.ban_duration = None
            else:
                raise ArgumentError(f"We do not accept {unit} as a time")
        else:
            self.ban_duration.hours = duration


        
