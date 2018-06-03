# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime
import time
import re

import builtins
import readline
from tabulate import tabulate

from database import TS_GROUP_BY


def prefill_input(prompt, empty_allowed, prefill=''):
    """Inputs a string with a prefilled value"""
    while True:
        readline.set_startup_hook(lambda: readline.insert_text(prefill))
        try:
            res = builtins.input(prompt)
        finally:
            readline.set_startup_hook()
        if not res and not empty_allowed:
            print("*** Error: Please input a non-empty value.")
            continue
        return res


def parse_extend_mask(mask):
    # check if the mask has valid values
    keywords = re.split(r'\||,', mask, re.U)
    # keywords = map(lambda x: x.strip(), keywords)
    bits = 0
    for key in keywords:
        if key not in TS_GROUP_BY:
            raise ValueError("*** Error: Unknown bitmask keyword '%s'" % key)
        bits |= TS_GROUP_BY[key]
    return bits


def print_project_info(project):
    '''Prints project info'''
    fields = ['ID: ', 'Name: ', 'Created: ', 'Description: ']
    info = zip(fields, project)
    print(tabulate(info))


def is_name_valid(name):
    """Validates a project's or task's name """
    error = "*** Error: Wrong name. Alphanumeric symbols are allowed only."
    try:
        groups = re.match(r'^(?P<name>\w+)$', name, re.U).groups()
    except AttributeError:
        raise ValueError(error)
    return groups


def parse_task_alias(arg):
    """Returns an encoded byte-strings of the parsed alias """
    """ as {'task': '<name>', 'project': '<name>'}"""
    error = "*** Error: Wrong '<task>#<project>' format. " \
            "Alphanumeric symbols and sharp are allowed only."
    try:
        return re.match(r'^(?P<task>\w+)#(?P<project>\w+)$',
                        arg, re.U).groupdict()
    except AttributeError:
        raise ValueError(error)


def parse_project_alias(arg):
    '''Returns the parsed alias as {'project': <name>, 'customer': <name>}'''
    groups = re.match(r'^(?P<project>\w+)(@(?P<customer>\w+))', arg, re.U)
    return groups.groupdict()


def parse_date(date_string):
    '''Parses date string'''
    return datetime.datetime.strptime(date_string, '%x').date()


def parse_date_parameters(args):
    """Parses date parameters from CLI. Returns a tuple of started and
finished dates."""
    """Format: [<from> [<to>]] | [today|[d]week|[d]month|[d]year|all]
           <from>|<to> - '<date>' | 'today'
    """
    error = "*** Error: Unknown date. Use national representation of the date " \
            "(e.g. '%s' for today)." \
            "" % datetime.date.strftime(
                datetime.date.today(), "%x").encode('utf-8')
    if not args:
        raise ValueError(error)
    args = [arg.lower() for arg in args]
    finished = today = datetime.date.today()
    day_delta = re.search(r'^-(\d+)$', args[0])
    if day_delta:
        # Allow to specify the time period as a '-N' value
        started = finished - datetime.timedelta(days=int(day_delta.groups()[0]))
    elif args[0] == 'dweek':
        started = finished - datetime.timedelta(days=7)
    elif args[0] == 'week':
        started = finished - datetime.timedelta(days=finished.weekday())
    elif args[0] == 'dmonth':
        started = finished - datetime.timedelta(days=31)
    elif args[0] == 'month':
        started = finished.replace(finished.year, finished.month, 1)
    elif args[0] == 'dyear':
        started = finished - datetime.timedelta(days=365)
    elif args[0] == 'year':
        started = finished.replace(finished.year, 1, 1)
    elif args[0] == 'all':
        started = datetime.date.fromtimestamp(0)
    elif args[0] == 'today':
        started = today
    else:
        # Parse <from>/<to> date parameters
        try:
            started = parse_date(args[0])
        except ValueError:
            raise ValueError(error)
        # Only one date presents
        finished = started
    if len(args) > 1:
        if args[1] == 'today':
            finished = today
        else:
            try:
                finished = parse_date(args[1])
            except ValueError:
                # the second parameter is not a date
                raise ValueError(error)
    return started, finished


def time_to_display(t):
    return time.strftime('%c', time.localtime(t))


def datetime_to_store(d):
    return time.mktime(d.timetuple())


def structure_as_human(weeks, days, hours, minutes, seconds):
    human = [
        "%dw" % weeks if weeks else '',
        "%d days" % days if days else '',
        "%dh:%02dm:%02ds" % (hours, minutes, seconds)
        #"%dh" % hours if hours else '',
        #"%dmin" % minutes if minutes else '',
        #"%dsec" % seconds if seconds else ''
    ]
    return ' '.join(filter(lambda x: x, human))


def seconds_to_human(total_seconds):
    weeks = total_seconds // (3600 * 24 * 7)
    seconds_per_week = weeks * 3600 * 24 * 7
    days = (total_seconds - seconds_per_week) // (3600 * 24)
    seconds_per_days = days * 3600 * 24
    hours = (total_seconds - seconds_per_week - seconds_per_days) // 3600
    seconds_per_hours = hours * 3600
    minutes = (total_seconds - seconds_per_week -
               seconds_per_days - seconds_per_hours) // 60
    seconds_per_minutes = minutes * 60
    seconds = total_seconds - seconds_per_week - seconds_per_days - \
        seconds_per_hours - seconds_per_minutes
    #print(total_seconds, weeks, days, hours, minutes, seconds)
    return structure_as_human(weeks, days, hours, minutes, seconds)


def timedelta_to_human(d):
    """ Returns timedelta as humans '3d 23h 1m 45s' """
    days = d.days
    hours = d.seconds // 3600
    per_hours = hours * 3600
    minutes = (d.seconds - hours * 3600) // 60
    per_minutes = minutes * 60
    seconds = d.seconds - per_hours - per_minutes
    return structure_as_human(0, days, hours, minutes, seconds)


def get_yes_no(default='y'):
    yes = ['y', 'yes']
    no = ['n', 'no']

    while True:
        choice = builtins.input().lower()
        empty_yes = not choice and default in yes
        if empty_yes or choice in yes:
            return True
        empty_no = not choice and default in no
        if empty_no or choice in no:
            return False
        print("Please respond with 'yes' or 'no' [y/n] ", end='')
