import re


def format_int(num):
    num = '%s' % num
    new = re.sub('(\d+)(\d{3})(,|$)', '\g<1>,\g<2>', num)
    if new != num:
        return format_int(new)
    return new

def format_rate(num):
    units = ['B', 'K', 'M', 'G', 'T']
    i = 0
    while num > 1023:
        i += 1
        num /= 1024
    return '{0}{1}/s'.format(num, units[i])

def format_eta(num):
    unit = 's'
    if num > 59:
        num /= 60
        unit = 'm'
    if num > 59:
        num /= 60
        unit = 'h'
    if num > 23:
        num /= 24
        unit = 'd'
    return '{0}{1}'.format(num, unit)


