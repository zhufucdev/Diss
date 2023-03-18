from gdey075z08_driver.driver import EPD
from PIL import Image, ImageDraw, ImageFont


def main(epd: EPD):
  img = Image.new('L', (800, 480), color=255)
  draw = ImageDraw.Draw(img)
  epd.display_frame(epd.get_frame_buffer(img))

if __name__ == '__main__':
  epd = EPD()
  epd.init()
  try:
    main(epd)
  finally:
    epd.sleep()