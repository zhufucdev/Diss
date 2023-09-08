from gdey075z08_driver.driver import EPD, EPD_HEIGHT, EPD_WIDTH
import PIL.Image as Image

epd = EPD()
img = Image.new('L', (EPD_WIDTH, EPD_HEIGHT), 255)
epd.init()
epd.display_frame(epd.get_frame_buffer(img))
epd.sleep()

