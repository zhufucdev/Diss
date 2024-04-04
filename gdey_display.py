import PIL.Image
from PIL.Image import Image
from gdey075z08_driver.driver import EPD, EPD_HEIGHT, EPD_WIDTH

from display import Display


class GdeyDisplay(Display):
    def __init__(self, accent_color: int):
        super().__init__((EPD_WIDTH, EPD_HEIGHT), False)
        self.__acc_color = accent_color
        self.__epd = EPD(red_bounds=(accent_color, accent_color + 1))

    def draw(self, canvas: Image):
        self.__epd.init()
        dithered = canvas.convert('1')
        drawing = PIL.Image.new('L', self.canvas_size)
        for y in range(self.canvas_size[1]):
            for x in range(self.canvas_size[0]):
                if canvas.getpixel(xy=(x, y)) == self.__acc_color:
                    drawing.putpixel(xy=(x, y), value=self.__acc_color)
                else:
                    drawing.putpixel(xy=(x, y), value=0 if dithered.getpixel((x, y)) == 0 else 255)

        self.__epd.display_frame(self.__epd.get_frame_buffer(drawing))
        self.__epd.sleep()
