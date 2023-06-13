from PIL.Image import Image

from display import Display


class LocalDisplay(Display):
    def __init__(self):
        super().__init__((800, 480))

    def draw(self, canvas: Image):
        canvas.show('display')
