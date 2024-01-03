from PIL.Image import Image
from gdey075z08_driver.driver import EPD, EPD_HEIGHT, EPD_WIDTH

from display import Display


class GdeyDisplay(Display):
    def __init__(self):
        super().__init__((EPD_WIDTH, EPD_HEIGHT))
        self.__epd = EPD(red_bounds=(253, 254))

    def draw(self, canvas: Image):
        self.__epd.init(),
        self.__epd.display_frame(self.__epd.get_frame_buffer(canvas)),
        self.__epd.sleep()
