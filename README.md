# Desktop Integrated Scheduling System

<div style="display: flex">
<img src="https://zhufucdev.com/api/images/EJ1yzDqW65gFJ9fWHTGoC" style="height: 200px; width: 200px; object-fit: cover; margin-right: 24px">

Some micro hardware project to bring the busy schedule
right in front of you
</div>




## How to build
Need some monitor, so that you can see the pixels

The one I choose is some GDEY075Z08 E-Paper display. If interested, buy one [here](https://www.good-display.com/product/394.html)

## How to program
### Driving the display
I wrote a graphic library for this project, namely epui. Check
its repo [here](https://github.com/zhufucdev/epui).

I also wrote a display driver, which can be found [here](https://github.com/zhufucdev/gdey075z08_driver).

This default driver, namely `EdeyDisplay`, is built for raspberrypi. 
If you want to reproduce in other platforms or for other screens,
just write yours.

```python
# your_display.py

from display import Display
from PIL.Image import Image

class YourDisplay(Display):
    def __init__(self):
        super().__init__((600, 480))
        
    def draw(self, canvas: Image):
        # Do some stuff with canvas
        pass
```

Just take YourDisplay instead
```diff
# main.py
# -- snip --

if __name__ == '__main__':
-   display = GdeyDisplay()
+   display = YourDisplay()

    img = Image.new('L', display.canvas_size, 255)
    draw = ImageDraw.Draw(img)
    context = construct_ui(draw, display.canvas_size)

    main(display, context, img)
```

### Private assets

You will never know my api keys. Instead, fill in yours
```shell
cd proper_res
echo 114514 >> caiyun_key
echo '{"something": "other things"}' >> client_secret.json # this is for Google Calendar
```

### Tests and previews

Like in [Driving the display](#driving-the-display), replace YourDisplay with LocalDisplay
```diff
# main.py
# -- snip --

if __name__ == '__main__':
-   display = YourDisplay()
+   display = LocalDisplay(800, 480)

    img = Image.new('L', display.canvas_size, 255)
    draw = ImageDraw.Draw(img)
# -- even more snip --
```

This time, your computer renders the 800x480 pixels high resolution image and pops the
window right in front of you
