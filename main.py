import sys

from display import Display
from gdey_display import GdeyDisplay

sys.path.append('./epui')

import schedule
import time
import threading

from epui.ui import *
from epui.schedule import GoogleCalendarProvider, CalendarView, SquareDateView, CalendarProvider, Event
from epui.weather import LargeWeatherView, WeatherTrendView, CaiYunWeatherProvider, Location, WeatherEffectiveness, \
    CaiYunAPIProvider
from PIL import Image, ImageDraw


class CachedCalendarProvider(CalendarProvider):
    def __init__(self, parent: CalendarProvider):
        self.__parent = parent
        self.__cache = None
        super().__init__(parent.get_name(), parent.get_max_results())

    def invalidate(self) -> bool:
        refreshed = self.__parent.get_events()
        if refreshed == self.__cache:
            return False
        self.__cache = refreshed
        return True

    def get_events(self) -> List[Event]:
        if self.__cache is None:
            self.invalidate()

        return self.__cache


def start_schedule(cached_provider: CachedCalendarProvider):
    while True:
        try:
            in_time = next((event for event in cached_provider.get_events() if time.localtime() in event.get_time()),
                           None)
            if not in_time or not in_time.get_location() or '楼' not in in_time.get_location():
                schedule.run_pending()
        except Exception as e:
            logging.error(e)
        time.sleep(10)


def construct_ui(draw, canvas_size: Tuple[int, int]) -> Context:
    resources.resources_dir.append('proper_res')

    context = Context(draw, canvas_size)
    vgroup = VGroup(context,
                    alignment=ViewAlignmentHorizontal.CENTER,
                    prefer=ViewMeasurement.default(
                        width=ViewSize.MATCH_PARENT,
                        height=ViewSize.MATCH_PARENT
                    ))
    header = HGroup(context,
                    prefer=ViewMeasurement.default(width=ViewSize.MATCH_PARENT),
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
    calendar_provider = CachedCalendarProvider(GoogleCalendarProvider(
        name='GCP',
        credentials_file=resources.get_file('client_secret.json'),
        max_results=4,
        callback_addr='0.0.0.0'
    ))

    calendar_view = CalendarView(
        context,
        provider=calendar_provider,
        font=resources.get_file('NotoSansCJKBold') or TextView.default_font,
        prefer=ViewMeasurement.default(
            size=ViewSize.MATCH_PARENT,
            margin_top=20,
            margin_bottom=20,
        )
    )

    large_weather_view = LargeWeatherView(
        context,
        provider=weather_provider,
        prefer=ViewMeasurement.default(margin=20)
    )

    weather_trend_view = WeatherTrendView(
        context,
        title='24 hours',
        provider=weather_provider,
        effect=WeatherEffectiveness.HOURLY,
        value=lambda w: w.temperature,
        line_width=3,
        prefer=ViewMeasurement.default(
            size=ViewSize.MATCH_PARENT,
        )
    )

    header.add_views(
        SquareDateView(
            context,
            prefer=ViewMeasurement.default(
                height=ViewSize.MATCH_PARENT,
                width=180
            ),
            current_week_offset=-6),
        large_weather_view,
        calendar_view
    )
    vgroup.add_view(weather_trend_view)

    def refresh_calendar():
        if calendar_provider.invalidate():
            calendar_view.refresh()

    def refresh_weather():
        weather_provider.invalidate()
        weather_trend_view.refresh()
        large_weather_view.refresh()

    schedule.every(3).minutes.do(refresh_calendar)
    schedule.every(3).hours.do(refresh_weather)
    threading.Thread(target=start_schedule, args=[calendar_provider]).start()
    return context


def main(display: Display, context: Context, img: Image.Image):
    context.on_redraw(lambda: display.draw(img))
    context.set_panic_handler(lambda x: logging.critical(x, exc_info=True))
    context.start()


if __name__ == '__main__':
    display = GdeyDisplay()

    img = Image.new('L', display.canvas_size, 255)
    draw = ImageDraw.Draw(img)
    context = construct_ui(draw, display.canvas_size)

    main(display, context, img)
