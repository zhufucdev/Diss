import argparse
import datetime
import sys

import requests

from display import Display

sys.path.append('./epui')

import schedule
import time
import threading

from epui.ui import *
from epui.schedule import GoogleCalendarProvider, CalendarView, SquareDateView, CalendarProvider, Event
from epui.weather import LargeWeatherView, Location, WeatherEffectiveness, \
    WeatherFlowView, WeatherProvider, Weather, HeFengWeatherProvider, HeFengAPIProvider
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


class SlicedWeatherProvider(WeatherProvider):
    def __init__(self, parent: WeatherProvider, ranging: range):
        super().__init__(location=parent.get_location(), temperature_unit=parent.get_temperature_unit())
        self.__parent = parent
        self.__range = ranging

    def get_weather(self) -> List[Weather]:
        return self.__parent.get_weather()[self.__range.start:self.__range.stop]


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


def gen_commit_message_getter():
    commit = {
        'text': '',
        'time': datetime.datetime.now()
    }

    def getter():
        if not commit['text'] == '' and datetime.datetime.now() - commit['time'] < datetime.timedelta(
                seconds=30):
            return commit['text']
        res = requests.get('https://whatthecommit.com/index.txt')
        commit['time'] = datetime.datetime.now()
        text = res.text.strip()
        i = 5
        j = 0
        while i < len(text):
            t = i
            while t < len(text) and not text[t].isspace():
                t += 1
            if t >= len(text):
                t = i
                while t > j and not text[t].isspace():
                    t -= 1
            if t == -1:
                text = text[0:i] + '\\\n' + text[i:]
            else:
                i = t
                text = text[0:i] + ' \\\n' + text[i + 1:]
            j = i
            i += 10
        text = f'$ git commit -m\\\n{text}'
        commit['text'] = text
        return text

    return getter


def construct_ui(draw, canvas_size: Tuple[int, int]) -> Context:
    resources.resources_dir.append('proper_res')

    context = Context(draw, canvas_size)
    hgroup_root = HGroup(context, prefer=ViewMeasurement.default(size=ViewSize.MATCH_PARENT))
    vgroup_left = VGroup(context,
                         alignment=ViewAlignmentHorizontal.CENTER,
                         prefer=ViewMeasurement.default(height=ViewSize.MATCH_PARENT))
    vgroup_right = VGroup(context,
                          alignment=ViewAlignmentHorizontal.CENTER,
                          prefer=ViewMeasurement.default(size=ViewSize.MATCH_PARENT))
    header = HGroup(context,
                    prefer=ViewMeasurement.default(width=ViewSize.MATCH_PARENT),
                    alignment=ViewAlignmentVertical.CENTER)
    vgroup_left.add_view(header)
    hgroup_root.add_views(vgroup_left, vgroup_right)
    context.root_group.add_view(hgroup_root)

    with open(resources.get_file('hefeng_key'), 'rb') as f:
        weather_api_provider = HeFengAPIProvider(
            api_key=f.read().decode('utf-8'),
            location=Location(
                latitude=32.20635,
                longitude=118.00113
            )
        )

    weather_provider = HeFengWeatherProvider(
        weather_api_provider
    )
    weather_provider_front = SlicedWeatherProvider(weather_provider, range(0, 12))
    weather_provider_rear = SlicedWeatherProvider(weather_provider, range(12, -1))
    with open(resources.get_file('gcp_key'), 'rb') as f:
        cid, key = f.read().decode('utf-8').splitlines()
        calendar_provider = CachedCalendarProvider(GoogleCalendarProvider(
            name='GCP',
            calendar_id=cid,
            api_key=key,
            max_results=8,
        ))

    calendar_view = CalendarView(
        context,
        provider=calendar_provider,
        font=resources.get_file('NotoSansCJKBold') or TextView.default_font,
        prefer=ViewMeasurement.default(
            size=ViewSize.MATCH_PARENT,
            margin_top=20,
        )
    )

    large_weather_view = LargeWeatherView(
        context,
        provider=weather_provider,
        prefer=ViewMeasurement.default(margin=20)
    )

    commit_view = TextView(
        context,
        text=gen_commit_message_getter(),
        font_size=26,
        align_vertical=ViewAlignmentVertical.CENTER,
        align_horizontal=ViewAlignmentHorizontal.CENTER,
        prefer=ViewMeasurement.default(size=ViewSize.MATCH_PARENT),
        font=resources.get_file('CommitMonoNerdFont-Regular')
    )

    def default_weather_flow(provider: WeatherProvider):
        return WeatherFlowView(
            context,
            provider=provider,
            effect=WeatherEffectiveness.HOURLY,
            prefer=ViewMeasurement.default(
                width=ViewSize.MATCH_PARENT,
            )
        )

    weather_grid = VGroup(context, prefer=ViewMeasurement.default(width=ViewSize.MATCH_PARENT))
    weather_grid.add_views(
        default_weather_flow(weather_provider_front),
        default_weather_flow(weather_provider_rear)
    )
    vgroup_right.add_view(weather_grid)

    header.add_views(
        SquareDateView(
            context,
            prefer=ViewMeasurement.default(
                height=ViewSize.MATCH_PARENT,
                width=180
            ),
            first_week='2023-08-22'),
        large_weather_view,
    )
    vgroup_left.add_view(calendar_view)
    vgroup_right.add_view(commit_view)

    def refresh_calendar():
        if calendar_provider.invalidate():
            calendar_view.refresh()

    def refresh_weather():
        weather_provider.invalidate()
        for view in weather_grid.get_children():
            view.refresh()
        large_weather_view.refresh()

    schedule.every(3).minutes.do(refresh_calendar)
    schedule.every(3).hours.do(refresh_weather)
    schedule.every(3).minutes.do(commit_view.invalidate)
    threading.Thread(target=start_schedule, args=[calendar_provider]).start()
    return context


def main(display: Display, context: Context, img: Image.Image):
    context.on_redraw(lambda: display.draw(img))
    context.set_panic_handler(lambda x: logging.critical(x, exc_info=True))
    context.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-b', '--bounds', action='store_true', help='Show bounds')
    args = parser.parse_args()

    if args.debug:
        from local_display import LocalDisplay

        display = LocalDisplay(800, 480)
    else:
        from gdey_display import GdeyDisplay

        display = GdeyDisplay()

    View.draw_bounds_box = args.bounds

    img = Image.new('L', display.canvas_size, 255)
    draw = ImageDraw.Draw(img)
    context = construct_ui(draw, display.canvas_size)

    main(display, context, img)
