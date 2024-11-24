import argparse
import datetime
import sys
import xmlrpc.client

import requests

sys.path.append('./epui')

import schedule
import time
import threading
import io
from xmlrpc.server import SimpleXMLRPCServer

from epui.ui import *
from epui.schedule import GoogleCalendarProvider, CalendarView, SquareDateView, CalendarProvider, Event
from epui.weather import LargeWeatherView, Location, WeatherEffectiveness, \
    WeatherFlowView, WeatherProvider, Weather, HeFengWeatherProvider, HeFengAPIProvider
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


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


def gen_commit_message_getter():
    commit = {
        'text': '',
        'time': datetime.datetime.now()
    }

    def getter(initial: int = 30, increment: int = 31, break_threshold: int = 6):
        if not commit['text'] == '' and datetime.datetime.now() - commit['time'] < datetime.timedelta(
                seconds=30):
            return commit['text']
        commit['time'] = datetime.datetime.now()
        res = requests.get('https://whatthecommit.com/index.txt')
        text = res.text.strip(' \n')
        i = initial
        while i < len(text):
            t = i
            while t < len(text) and t - i < break_threshold and not text[t].isspace():
                t += 1
            if t >= len(text):
                break
            elif t - i >= break_threshold:
                text = text[0:i] + '\\\n' + text[i:]
            else:
                i = t
                text = text[0:i] + ' \\\n' + text[i + 1:]
            i += increment
        text = f'[\uf43a {datetime.datetime.now().strftime("%H:%M:%S")}]\n$ git commit -m \\\n{text}'
        commit['text'] = text
        return text

    return getter


def construct_ui(draw, canvas_size: tuple[int, int], api_addr: str | None) -> Context:
    context = Context(draw, canvas_size, accent_color=253)
    resources.resources_dir.append('proper_res')

    vgroup_root = VGroup(context, prefer=ViewMeasurement.default(size=ViewSize.MATCH_PARENT))
    header = HGroup(context,
                    prefer=ViewMeasurement.default(width=ViewSize.MATCH_PARENT))
    tail = HGroup(context,
                  prefer=ViewMeasurement.default(width=ViewSize.MATCH_PARENT, margin_top=20))
    vgroup_root.add_views(header, tail)
    context.root_group.add_view(vgroup_root)

    with open(resources.get_file('hefeng_key'), 'rb') as f:
        weather_api_provider = HeFengAPIProvider(
            api_key=f.read().decode('utf-8'),
            location=Location(
                latitude=32.20635,
                longitude=118.00113
            )
        )

    weather_provider = HeFengWeatherProvider(
        context,
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

    large_weather_view = LargeWeatherView(
        context,
        provider=weather_provider,
        prefer=ViewMeasurement.default(margin=20)
    )

    calendar_view = CalendarView(
        context,
        provider=calendar_provider,
        font=resources.get_file('NotoSansCJKBold') or TextView.default_font,
        prefer=ViewMeasurement.default(height=ViewSize.WRAP_CONTENT, width=400, margin_right=20, margin_left=20)
    )

    commit_view = TextView(
        context,
        text=gen_commit_message_getter(),
        font_size=16,
        font=resources.get_file('CommitMonoNerdFont-Regular'),
        prefer=ViewMeasurement.default(width=ViewSize.MATCH_PARENT)
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

    header.add_views(
        SquareDateView(
            context,
            prefer=ViewMeasurement.default(
                height=ViewSize.MATCH_PARENT,
                width=180
            ),
            first_week='2024-09-02'),
        large_weather_view,
        weather_grid
    )
    tail.add_views(calendar_view, commit_view)

    def refresh_calendar():
        if calendar_provider.invalidate():
            calendar_view.refresh()

    def refresh_weather():
        weather_provider.invalidate()
        for view in weather_grid.get_children():
            view.invalidate()
        large_weather_view.refresh()

    def setup_rpc_server(listen_addr: str):
        split = listen_addr.split(':')
        server = SimpleXMLRPCServer((split[0], int(split[1])), allow_none=True)

        @server.register_function()
        def display(binary: xmlrpc.client.Binary, idle: float):
            buf = io.BytesIO()
            buf.write(binary.data)
            buf.seek(0)
            image = Image.open(buf).convert('L')
            original = context.root_group.get_children()
            context.root_group.clear()
            context.root_group.add_view(
                ImageView(context, image, prefer=ViewMeasurement.default(size=ViewSize.MATCH_PARENT)))

            def recover():
                sleep(idle)
                context.root_group.clear()
                context.root_group.add_views(*original)

            threading.Thread(target=recover).start()

        threading.Thread(target=server.serve_forever).start()
        logging.info(f'rpc on {listen_addr}')

        return server

    def start_schedule():
        if api_addr:
            server = setup_rpc_server(api_addr)

        while not context.status == EventLoopStatus.STOPPED:
            try:
                in_time = next(
                    (event for event in calendar_provider.get_events() if time.localtime() in event.get_time()), None)
                if not in_time or not in_time.get_location() or '楼' not in in_time.get_location():
                    schedule.run_pending()
            except Exception as e:
                logging.critical(e, exc_info=True)
            time.sleep(10)

        if api_addr:
            server.shutdown()

    schedule.every(3).minutes.do(refresh_calendar)
    schedule.every(3).hours.do(refresh_weather)
    schedule.every(30).minutes.do(commit_view.invalidate)
    threading.Thread(target=start_schedule).start()
    return context


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-b', '--bounds', action='store_true', help='Show bounds')
    parser.add_argument('-l', '--listen', help='API address, or disable if none', const='localhost:9090', default=None,
                        nargs='?')
    args = parser.parse_args()

    if args.debug:
        from local_display import LocalDisplay

        display = LocalDisplay(800, 480, 253)
    else:
        from gdey_display import GdeyDisplay

        display = GdeyDisplay(accent_color=253)

    View.draw_bounds_box = args.bounds

    img = Image.new('L', display.canvas_size, 255)
    draw = ImageDraw.Draw(img)

    context = construct_ui(draw, display.canvas_size, args.listen)
    context.on_redraw(lambda: display.draw(img))
    context.set_panic_handler(lambda x: logging.critical(x, exc_info=True))
    context.start()
    logging.info('context started')
    display.start()
    if display.is_blocking:
        context.destroy()
    else:
        display.start()


if __name__ == '__main__':
    main()
