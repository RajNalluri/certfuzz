#!/usr/bin/env python
'''
Created on April 28, 2013

@organization: cert.org
'''
import logging
import os
import re
from subprocess import Popen

try:
    from certfuzz.fuzztools.filetools import mkdir_p, all_files, copy_file
    from certfuzz import debuggers
    from certfuzz.file_handlers.basicfile import BasicFile
    from certfuzz.runners.runner_base import get_command_args_list
    from certfuzz.campaign.config.bff_config import ConfigHelper, read_config_options
    from certfuzz.debuggers import gdb  # @UnusedImport
except ImportError:
    # if we got here, we probably don't have .. in our PYTHONPATH
    import sys
    mydir = os.path.dirname(os.path.abspath(__file__))
    parentdir = os.path.abspath(os.path.join(mydir, '..'))
    sys.path.append(parentdir)
    from certfuzz.fuzztools.filetools import mkdir_p, all_files, copy_file
    from certfuzz import debuggers
    from certfuzz.file_handlers.basicfile import BasicFile
    from certfuzz.runners.runner_base import get_command_args_list
    from certfuzz.campaign.config.bff_config import ConfigHelper, read_config_options
    from certfuzz.debuggers import gdb  # @UnusedImport

logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def parseiterpath(commandline):
    # Return the path to the iteration's fuzzed file
    for part in commandline.split():
        if 'bff-crash' in part:
            return part


def getiterpath(gdbfile):
    # Find the commandline in an msec file
    with open(gdbfile) as gdblines:
        for line in gdblines:
            m = re.match('Running: ', line)
            if m:
                return parseiterpath(line)


def main():
    debuggers.verify_supported_platform()

    from optparse import OptionParser

    hdlr = logging.StreamHandler()
    logger.addHandler(hdlr)

    usage = "usage: %prog [options] fuzzedfile"
    parser = OptionParser(usage)
    parser.add_option('', '--debug', dest='debug', action='store_true',
                      help='Enable debug messages (overrides --verbose)')
    parser.add_option('', '--verbose', dest='verbose', action='store_true',
                      help='Enable verbose messages')
    parser.add_option('-c', '--config', default='conf.d/bff.cfg',
                      dest='config', help='path to the configuration file to use')
    parser.add_option('-e', '--edb', dest='use_edb',
                      action='store_true',
                      help='Use edb instead of gdb')
    parser.add_option('-p', '--debugger', dest='debugger',
                      help='Use specified debugger')
    parser.add_option('-f', '--filepath', dest='filepath',
                      action='store_true', help='Recreate original file path')

    (options, args) = parser.parse_args()

    if options.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    cfg_file = options.config
    logger.debug('Config file: %s', cfg_file)

    if len(args) and os.path.exists(args[0]):
        fullpath_fuzzed_file = os.path.abspath(args[0])
        fuzzed_file = BasicFile(fullpath_fuzzed_file)
        logger.info('Fuzzed file is %s', fuzzed_file)
    else:
        parser.error('fuzzedfile must be specified')

    iterationpath = ''

    if options.filepath:
        # Recreate same file path as fuzz iteration
        resultdir = os.path.dirname(fuzzed_file.path)
        for gdbfile in all_files(resultdir, '*.gdb'):
            print '** using gdb: %s' % gdbfile
            iterationpath = getiterpath(gdbfile)
            break
        iterationdir = os.path.dirname(iterationpath)
        iterationfile = os.path.basename(iterationpath)
        if iterationdir:
            mkdir_p(iterationdir)
            copy_file(fuzzed_file.path,
                      os.path.join(iterationdir, iterationfile))
            fullpath_fuzzed_file = iterationpath

    config = read_config_options(cfg_file)

    cmd_as_args = config.get_command_list(fullpath_fuzzed_file)
    program = cmd_as_args[0]
    if not os.path.exists(program):
        # edb wants a full path to the target app, so let's find it
        for path in os.environ["PATH"].split(":"):
                if os.path.exists(os.path.join(path, program)):
                    program = os.path.join(path, program)

    # Recreate command args list with full path to target
    cmd_as_args = []
    cmd_as_args.append(program)
    cmd_as_args.extend(config.get_command_args_list(fullpath_fuzzed_file))

    args = []

    if options.use_edb and options.debugger:
        parser.error('Options --edb and --debugger are mutually exclusive.')

    if options.debugger:
        debugger_app = options.debugger
    elif options.use_edb:
        debugger_app = 'edb'
    else:
        debugger_app = 'gdb'
    args.append(debugger_app)

    if options.use_edb:
        args.append('--run')
    else:
        # Using gdb
        args.append('--args')
    args.extend(cmd_as_args)
    logger.info('args %s' % args)

    p = Popen(args, universal_newlines=True)
    p.wait()

if __name__ == '__main__':
    main()
