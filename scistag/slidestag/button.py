from widget import Widget, PaintEvent, Color


class Button(Widget):
    """
    A simple button control
    """

    def __init__(self, parent: Widget, parameters: dict):
        """
        Intitializer

        :param parent: The parent widget
        :param parameters: The creation parameters. See Widget. In addition:
        text: The button's text
        """
        super().__init__(parent, **parameters)

    def handle_paint(self, event: PaintEvent) -> bool:
        canvas = event.canvas
        canvas.rect(pos=(0, 0), size=self.size, color=Color(0, 0, 1.0))
        return super().handle_paint(event)
