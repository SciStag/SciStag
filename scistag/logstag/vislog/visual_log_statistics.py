from dataclasses import dataclass


@dataclass
class VisualLogStatistics:
    update_rate: float
    update_counter: int
    uptime: float
