from PIL.Image import Image

from display import Display


class LocalDisplay(Display):
    def __init__(self, width: int, height: int):
        super().__init__((width, height))

    def draw(self, canvas: Image):
        canvas.show('display')
