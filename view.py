from PIL import ImageDraw
from typing import *

class View:
  def __init__(self) -> None:
    pass


class Group(View):
  def __init__(self, children: List[View]) -> None:
    self.children = children


def draw_view(draw: ImageDraw.ImageDraw, view):
  pass