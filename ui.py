from PIL import ImageDraw
from typing import *
from time import sleep
from threading import Thread
from enum import Enum

import resources

RELOAD_INTERVAL = 2
RELOAD_AWAIT = 1 # delay 1 second before each global invalidation

class EventLoopStatus(Enum):
  NOT_LOADED = 1
  RUNNING = 2
  STOPPED = 3

class Context:
  """
  A Context is shared btween all its subviews to provide drawing functionality
  """
  def __init__(self, canvas: ImageDraw.ImageDraw, size: Tuple[float, float], scale: float = 1) -> None:
    self.__status = EventLoopStatus.NOT_LOADED
    self.root_group = Group(self)
    self.__requests = 0
    self.__main_canvas = canvas
    self.canvas_size = size
    self.scale = scale
    self.__redraw_listener = None

    self.__event_loop = Thread(target=self.__start_event_loop)

  def request_redraw(self):
    """
    Mark the current status as to invalidate
    """
    self.__requests += 1

  def __start_event_loop(self):
    self.__status = EventLoopStatus.RUNNING
    current_requests = self.__requests
    while self.__status == EventLoopStatus.RUNNING:
      current_requests = self.__requests
      if current_requests > 0:
        sleep(RELOAD_AWAIT)
        if current_requests == self.__requests:
          self.__requests = 0
          self.__main_canvas.rectangle([0, 0, self.canvas_size[0], self.canvas_size[1]], fill=255) # clear canvas
          self.root_group.draw(self.__main_canvas, self.canvas_size, self.scale)
          if self.__redraw_listener:
            self.__redraw_listener()

      sleep(RELOAD_INTERVAL)
  
  def on_redraw(self, listener):
    self.__redraw_listener = listener

  def start(self):
    self.__event_loop.setName('event_loop')
    self.__event_loop.start()
    self.__event_loop.join()

  def destroy(self):
    """
    Mark the current status as stopped, and wait for the
    event loop to finish
    """
    if self.__status == EventLoopStatus.STOPPED:
      raise RuntimeError('Current context already stopped')
    
    self.__status = EventLoopStatus.STOPPED
    self.__event_loop.join()



class View:
  def __init__(self, context: Context) -> None:
    self.context = context
  
  def invalidate(self):
    self.context.request_redraw()

  def draw(self, canvas: ImageDraw.ImageDraw, size: Tuple[float, float], scale: float):
    place_holder = resources.get('view-gallery')
    def fit(rate):
      return place_holder.resize((place_holder.size[0] * rate, place_holder.size[1] * rate))

    if size[0] > 64 and size[1] > 64:
      _size = (size[0] - 64 * scale, size[1] - 64 * scale) # margin

    if not (_size[0] > place_holder.size[0] and _size[1] > place_holder.size[1]):
      if place_holder.size[0] > place_holder.size[1]:
        place_holder = fit(_size[0] / place_holder.size[0])
      else:
        place_holder = fit(_size[1] / place_holder.size[1])
    
    canvas.bitmap([(size[0] - place_holder.size[0]) / 2, (size[1] - place_holder.size[1]) / 2], place_holder)
    canvas.rectangle(((0, 0), (size[0], size[1])), fill=None, outline=0, width=6 * scale)


class Group(View):
  def __init__(self, context: Context) -> None:
    self.__children = []
    self.measuremenets = {}
    super().__init__(context)

  def add_view(self, child: View):
    self.__children.append(child)
    self.measuremenets[child] = self.measure(child)
    self.context.request_redraw()

  def draw(self, canvas: ImageDraw.ImageDraw, size: Tuple[float, float], scale: float):
    for child in self.__children:
      child.draw(canvas, size, scale)

  def measure(self, child: View) -> Tuple[float, float]:
    pass
