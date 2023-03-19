from gdey075z08_driver.driver import EPD, EPD_HEIGHT, EPD_WIDTH
from PIL import Image, ImageDraw
from ui import *
from threading import Thread

def construct_ui(draw) -> Context:
  main_context = Context(draw, [EPD_WIDTH, EPD_HEIGHT])
  main_context.root_group.add_view(
    View(main_context)
  )
  main_context.request_redraw()
  return main_context


def main(epd: EPD, context: Context, img: Image.Image):
  context.on_redraw(lambda: [epd.display_frame(epd.get_frame_buffer(img)), epd.delay_ms(100), epd.sleep()])
  context.start()

if __name__ == '__main__':
  epd = EPD()
  epd.init()
  img = Image.new('L', (EPD_WIDTH, EPD_HEIGHT), 255)
  draw = ImageDraw.Draw(img)
  context = construct_ui(draw)
  
  try:
    main(epd, context, img)
  finally:
    context.destroy()
    with Thread(target=epd.sleep) as t:
      t.start()
      t.join(2)

    