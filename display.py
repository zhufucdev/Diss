from typing import Tuple
from PIL.Image import Image


class Display:
    def __init__(self, canvas_size: Tuple[int, int], is_blocking: bool):
        self.canvas_size = canvas_size
        self.is_blocking = is_blocking

    def start(self) -> bool:
        """
        Start the display, probably blocking
        """
        return False

    def draw(self, canvas: Image):
        pass
