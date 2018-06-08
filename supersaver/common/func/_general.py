import os
import random
import string


def datetime_ignore_ms_equal(t1, t2):
    return (t1.year == t2.year
            and t1.month == t2.month
            and t1.day == t2.day
            and t1.hour == t2.hour
            and t1.minute == t2.minute
            and t1.second == t2.second)


def remove_duplicate_spaces(s):
    if s is None or len(s) < 2:
        return s
    out_s, is_space = '', False
    for c in s:
        if is_space and (c == ' '):
            continue
        else:
            is_space = (c == ' ')
            out_s += c
    return out_s


PS_OUTPUT_COLUMNS = 11


def get_processes(process_name_prefix):
    ps_process = os.popen('ps aux')
    process_info = ps_process.readlines()
    processes = []
    for process_line in process_info:
        process_line = remove_duplicate_spaces(process_line.strip('\n'))
        items = process_line.split(' ', PS_OUTPUT_COLUMNS - 1)
        if len(items) != PS_OUTPUT_COLUMNS:
            continue
        command = items[10]
        if command.startswith(process_name_prefix):
            processes.append((int(items[1]), command))
    return processes


def random_string(length, charset=(string.ascii_letters + string.digits)):
    rand = random.SystemRandom()
    return ''.join([rand.choice(charset) for _ in range(length)])


def retry(max_retry, func, *args, **kwargs):
    tried = 1
    while True:
        try:
            return func(*args, **kwargs)
        except:
            if tried < max_retry:
                tried += 1
                continue
            else:
                raise


def retry_if_exception(max_retry, exception_types, func, *args, **kwargs):
    tried = 1
    if isinstance(exception_types, list):
        exception_types = tuple(exception_types)
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, exception_types) and tried < max_retry:
                tried += 1
                continue
            else:
                raise


def calculate_size_by_long_edge(size, long_edge_length):
    w, h = size
    if w >= h:
        new_w = long_edge_length
        new_h = int(h * float(new_w) / float(w))
    else:
        new_h = long_edge_length
        new_w = int(w * float(new_h) / float(h))
    return new_w, new_h


def calculate_size_by_short_edge(size, short_edge_length):
    w, h = size
    if w >= h:
        new_h = short_edge_length
        new_w = int(w * float(new_h) / float(h))
    else:
        new_w = short_edge_length
        new_h = int(h * float(new_w) / float(w))
    return new_w, new_h


def get_optional_fields(source, fields):
    values = []
    for field in fields:
        if field in source:
            values.append(source[field])
        else:
            values.append(None)
    return values
