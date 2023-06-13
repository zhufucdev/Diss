from typing import Tuple
from PIL.Image import Image


class Display:
    def __init__(self, canvas_size: Tuple[int, int]):
        self.canvas_size = canvas_size

    def draw(self, canvas: Image):
        pass
