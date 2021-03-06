'''
Created on Oct 24, 2012

@organization: cert.org
'''
import platform
import random
import string
from pprint import pformat, pprint
import logging

my_os = platform.system()

def quoted(string_to_wrap):
    return '"%s"' % string_to_wrap

def print_dict(d):
    pprint(d)

def check_os_compatibility(expected_os, module_name=__name__):
    if not my_os == expected_os:
        template = 'Module %s is incompatible with %s (%s expected)'
        raise ImportError(template % (module_name, my_os, expected_os))

def random_str(length=1):
    chars = string.ascii_letters + string.digits
    return ''.join([random.choice(chars) for dummy in xrange(length)])

def bitswap(input_byte):
    bits = [1, 2, 4, 8, 16, 32, 64, 128]
    backwards = list(bits)
    backwards.reverse()
    # 1   -> 128
    # 2   -> 64
    # 4   -> 32
    # 8   -> 16
    # 16  -> 8
    # 32  -> 4
    # 64  -> 2
    # 128 -> 1
    output_byte = 0
    for x, y in zip(bits, backwards):
        # if bit x is set in input_byte,
        # set bit y in output_byte
        if input_byte & x:
            output_byte |= y
    return output_byte

def log_object(obj, logger, level=logging.DEBUG):
    for l in pformat(obj.__dict__).splitlines():
        logger.log(level, '%s', l)
