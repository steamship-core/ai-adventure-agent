from typing import List, Tuple


class RouteTiming:
    url: str
    call_count: int = 0
    total_time: float = 0

    def __init__(self, url: str):
        self.url = url

    def avg_time(self) -> float:
        return self.total_time / self.call_count

    def nice_url(self) -> str:
        if "/v1/" in self.url:
            return self.url[self.url.index("/v1/") + 4 :]
        else:
            return self.url


def pretty_print_timings(timings: List[Tuple[str, float]]):
    route_timings = {}
    for timing in timings:
        url = timing[0]
        time_taken = timing[1]
        if url not in route_timings:
            route_timings[url] = RouteTiming(url)
        route_timing = route_timings[url]
        route_timing.call_count = route_timing.call_count + 1
        route_timing.total_time = route_timing.total_time + time_taken

    route_timings_list = list(route_timings.values())
    route_timings_list.sort(key=lambda t: t.total_time, reverse=True)

    total_time = sum([route_timing.total_time for route_timing in route_timings_list])
    print("| Route          | Total Time | Num Calls | Avg Per | % of total |")
    for route_timing in route_timings_list:
        print(
            f"| {route_timing.nice_url():30} | {route_timing.total_time:.3f} | {route_timing.call_count:3} | {route_timing.avg_time():.3f} | {route_timing.total_time / total_time * 100: .1f} |"
        )
