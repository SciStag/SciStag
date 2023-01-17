from __future__ import annotations

from typing import Union

from pydantic import BaseModel

from scistag.vislog.options.log_options import APP_MODES


class LogRunOptions(BaseModel):
    """
    Options for defining the running behavior of the log, e.g. if it shall be run once
    or continuous.
    """

    mt: bool = True
    """
    Defines if the server shall be run in multithreading mode
    """
    continuous: Union[bool, None] = None
    """
    Defines if the run_server shall run until
    :meth:`LogBuilder.terminate` was called to update the logs content
    continuously."""
    wait: bool = True
    """Defines if also a non-continuous log shall wait till
    the log has been terminated. (via :meth:`terminate`) or the
    application was killed via Ctrl-C.

    Has no effect if threaded is False (because the server will anyway
    block the further execution then) or if continuous is set to True.

    Basically it acts like the "continuous" mode just with the
    difference that the builder function is just called once."""
    auto_clear: Union[bool, None] = None
    """Defines if then log shall be cleared automatically
    when being rebuild with `continuous=True`."""

    refresh_time_s: float = 0.25
    """
    The time interval with which the log shall be refreshed when using
    the liveViewer (see Live_view)
    """

    app_mode: APP_MODES = ""
    """
    Defines if the log shall behave like an application.

    In the future you will be able to set here an application class
    or instance. At the moment you can pass "cute" to open the app
    in a webkit built-in browser (requires the extra "cutestag") or
    an explicit installation of pyside6 (or above)."""

    def setup(
        self, app_mode: APP_MODES | None = None, refresh_time_s: float | None = None
    ):
        """
        Setups the startup behavior

        :param app_mode: If defined the sever will also automatically start either
            the default browser or the log in Qt's internal browser
        :param refresh_time_s: Defines the idle refresh time, so the time gap between
            how often a remote client at least asks for updates.
        """
        self.app_mode = app_mode if app_mode is not None else ""
        if refresh_time_s is not None:
            self.refresh_time_s = refresh_time_s

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
