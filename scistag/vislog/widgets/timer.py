"""
Implements the class :class:`LTimer` which lets the user set up a time which is either
scheduled once or in a defined interval.
"""

from __future__ import annotations

import time
from typing import Callable, Union

from scistag.vislog import LogBuilder
from scistag.vislog.widgets import LWidget, LEvent

TIMER_LOOP_EVENT_TYPE_IDENTIFIER = "TIMER_TICK_EVENT"


class LTimerTickEvent(LEvent):
    """The tick event is triggered by a LTimer in the configured frequency"""

    def __init__(self, **kwargs):
        super().__init__(event_type=TIMER_LOOP_EVENT_TYPE_IDENTIFIER, **kwargs)


class LTimer(LWidget):
    """
    The timer class allows the triggering of an event in either a defined time interval,
    after a specified delay or both in combination.

    It can be used to realize animations or handle or create events in a specific
    interval.
    """

    def __init__(
        self,
        builder: "LogBuilder",
        interval_s: float | None = None,
        delays_s: float | None = None,
        on_tick: Union[Callable, None] = None,
        enforce: bool = False,
        name: str = "",
        insert: bool = True,
    ):
        """
        :param builder: The builder to which the widget shall be added
        :param interval_s: The timer's trigger interval in seconds

            If None is passed the timer will only be executed once after delay_s
            seconds.
        :param delays_s: The delay before the initial tick is triggered in seconds
        :param enforce: Enforce the defined frequency if required to ensure a
            constant update rate. Note that your timer callback needs to be faster
            than the frequency, otherwise the system might end up in a sort of
            infinite loop.
        :param on_tick: The function to be called when the timer is triggered
        :param name: The timer's name
        :param insert: Defines if the element shall be inserted into the log
        """
        self.loop_counter = 0
        """Defines the count of executed loops"""
        self.frequency_s = interval_s if interval_s is not None else 0.0
        """The trigger frequency in seconds"""
        self.delays_s = delays_s
        """The initial delay in seconds"""
        self.enforce = enforce
        """Defines if the frequency shall be enforced"""
        super().__init__(builder=builder, name=name, is_view=False)
        self.next_execution = time.time() + (
            self.delays_s if delays_s is not None else 0.0
        )
        """The time stamp of the next execution"""
        self.on_tick = on_tick
        if insert:
            self.insert_into_page()

    def write(self):
        pass  # nothing to write, we are just virtual

    def handle_timer(self, event: LTimerTickEvent):
        """
        The handle_timer handler is called when ever the timer triggers

        :param event: The event
        """
        if self.on_tick is not None:
            self.on_tick()

    def handle_event(self, event: "LEvent"):
        if event.event_type == TIMER_LOOP_EVENT_TYPE_IDENTIFIER:
            event: LTimerTickEvent
            self.handle_timer(event)

    def handle_loop(self) -> float | None:
        if self.next_execution is None:
            return None
        may_trigger = time.time() > self.next_execution
        if not may_trigger:
            return self.next_execution
        cur_time = time.time()
        if self.frequency_s is not None:
            self.next_execution = self.next_execution + self.frequency_s
            if self.next_execution < cur_time and not self.enforce:
                self.next_execution = cur_time
        else:
            self.next_execution = None
        event = LTimerTickEvent(widget=self)
        self.raise_event(event)
        return self.next_execution
