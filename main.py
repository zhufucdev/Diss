import sys
sys.path.append('./epui')

import epui.cache as cache
import epui.resources as resources
from epui.ui import *
from epui.schedule import GoogleCalendarProvider, CalendarView, SquareDateView
from epui.weather import LargeWeatherView, WeatherTrendView, CaiYunWeatherProvider, Location, WeatherEffectiveness, CaiYunAPIProvider
from threading import Thread
from PIL import Image, ImageDraw
from gdey075z08_driver.driver import EPD, EPD_HEIGHT, EPD_WIDTH


def construct_ui(draw) -> Context:
    CANVAS_SIZE = (EPD_WIDTH, EPD_HEIGHT)
    resources.resources_dir.append('proper_res')

    context = Context(draw, CANVAS_SIZE)
    vgroup = VGroup(context,
                    alignment=ViewAlignmentHorizontal.CENTER,
                    prefer=ViewMeasurement.default(
                        width=ViewSize.MATCH_PARENT,
                        height=ViewSize.MATCH_PARENT
                    ))
    header = HGroup(context,
                    prefer=ViewMeasurement.default(
                        width=ViewSize.MATCH_PARENT),
                    alignment=ViewAlignmentVertical.CENTER)
    vgroup.add_view(header)
    context.root_group.add_view(vgroup)

    with open(resources.get_file('caiyun_key'), 'rb') as f:
        weather_api_provider = CaiYunAPIProvider(
            api_key=f.read().decode('utf-8'),
            location=Location(
                latitude=32.20635,
                longitude=118.00113
            )
        )

    weather_provider = CaiYunWeatherProvider(
        weather_api_provider
    )
    calendar_provider = GoogleCalendarProvider(
        name='GCP',
        credentials_file=resources.get_file('client_secret.json'),
        max_results=4,
        callback_addr='raspberrypi.local'
    )
    header.add_views(
        SquareDateView(
            context,
            prefer=ViewMeasurement.default(
                height=ViewSize.MATCH_PARENT,
                width=180
            ),
            current_week_offset=-5),
        LargeWeatherView(
            context,
            provider=weather_provider,
            prefer=ViewMeasurement.default(margin=20)
        ),
        CalendarView(
            context,
            provider=calendar_provider,
            font=resources.get_file('NotoSansCJKBold'),
            prefer=ViewMeasurement.default(
                size=ViewSize.MATCH_PARENT,
                margin_top=20,
                margin_bottom=20,
                margin_right=20
            )
        )
    )
    vgroup.add_views(
        WeatherTrendView(
            context,
            title='24 hours',
            provider=weather_provider,
            effect=WeatherEffectiveness.HOURLY,
            value=lambda w: w.temperature,
            prefer=ViewMeasurement.default(
                size=ViewSize.MATCH_PARENT,
            )
        )
    )
    return context


def main(epd: EPD, context: Context, img: Image.Image):
    context.on_redraw(lambda: [
        epd.display_frame(epd.get_frame_buffer(img)),
        img.save('last_redraw.png'),
        epd.sleep()
    ])
    # context.redraw_once()
    # epd.display_frame(epd.get_frame_buffer(img))
    context.start()


if __name__ == '__main__':
    epd = EPD(red_bounds=(90, 125))
    epd.init()
    img = Image.new('L', (EPD_WIDTH, EPD_HEIGHT), 255)
    draw = ImageDraw.Draw(img)
    context = construct_ui(draw)

    main(epd, context, img)
