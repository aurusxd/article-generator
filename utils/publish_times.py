from datetime import datetime, time, timedelta

def generate_publish_times(
    posts_per_day: int,
    start_hour: int = 9,
    end_hour: int = 21,
) -> list[time]:
    if posts_per_day <= 0:
        return []

    if posts_per_day == 1:
        return [time(hour=start_hour)]

    start = datetime.combine(datetime.today(), time(hour=start_hour))
    end = datetime.combine(datetime.today(), time(hour=end_hour))

    total_seconds = (end - start).total_seconds()
    interval = total_seconds / (posts_per_day - 1)

    return [
        (start + timedelta(seconds=interval * i)).time().replace(second=0, microsecond=0)
        for i in range(posts_per_day)
    ]


def is_time_to_publish(
    publish_time: time,
    window_minutes: int = 3,
) -> bool:
    now = datetime.now()
    target = datetime.combine(now.date(), publish_time)

    return abs(now - target) <= timedelta(minutes=window_minutes)

