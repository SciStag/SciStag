"""
Defines the page specific default options :class:`PageOptions`.
"""

from __future__ import annotations

from pydantic import BaseModel

import scistag


class PageOptions(BaseModel):
    """
    Option set for general page (default) properties.

    Note that in the future the page options will be (optionally) configurable on a
    per-page basis.
    """

    title: str = "SciStag - VisualLog"
    """The page's initial title"""

    footer_promo = (
        f'<p style="text-align: center"><small style="color: gray">Built '
        f'with <a style="color: gray" href="https://github.com/scistag/scis'
        f'tag">SciStag v{scistag.common.__version__}</a></small></p>'
    )
    """The footer promo. Thanks for not disabling it but you can of course if you
    want to"""

    def setup(self, title: str | None = None):
        """
        Setups the page options

        :param title: The page's title
        """
        if title is not None:
            self.title = title

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
