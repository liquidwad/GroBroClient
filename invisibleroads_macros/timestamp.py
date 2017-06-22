import datetime


def get_timestamp(with_microsecond=False):
    now = datetime.datetime.now()
    if with_microsecond:
        return now.strftime('%Y%m%d-%H%M-%f')
    else:
        return now.strftime('%Y%m%d-%H%M')
