# -*- coding: utf_8 -*-
from __future__ import print_function

import atexit
import datetime
import locale
import os
import re
import sys
import readline
import shlex
import operator
from cmd import Cmd
from subprocess import call
from tempfile import NamedTemporaryFile
import ConfigParser

from tabulate import tabulate
import builtins

import config
import helpers
from contrib import (__version__, __release_date__, __author__, __email__)
from database import TS_GROUP_BY, Database
import errors


class BTShell(Cmd):
    bloody_prompt = 'bloody'
    default_intro = 'Welcome to Bloody Tracker. Type help or ? to list ' \
            'commands.{eol}'.format(eol=os.linesep)
    intro = str(
        "{eol}                __,--,'              "
        "{eol}           x,--'      \\\\      Welcome to Bloody Tracker V{ver}."
        "{eol}          /|\\           \\`.                               _.-> X"
        "{eol}         / | \\  ` 10ccm  \\ `.                           .'    "
        "{eol}        /  |  \\           \\  `/             _.--.      /      "
        "{eol}       / ' |:  \\       `:  \\              .'     `.__.'       "
        "{eol}      / ,  |    \\         _,\\            /                    "
        "{eol}    \\'|   / \\  ' \\    _,-'_| `.         o          "
        "{eol}     /`._;   \\   |\\,-'_,-'     ` /            Type help or ? to "
        "{eol}   \\'     `- '`-.|_,`'.                              list commands."
        "{eol}                        `/"
    ).format(eol=os.linesep, ver=__version__)

    error_wrong_parameters = '*** Error: Wrong parameters.'

    def set_prompt(self, ps1=''):
        """Set prompt to active task"""
        if not ps1:
            task = self.db.get_active_task()
            if task:
                ps1 = ('%s#%s' % (task['tname'], task['pname'])).encode('utf8')
            else:
                ps1 = self.bloody_prompt
        self.prompt = ('(%s)> ' % ps1)

    def init_config(self):
        error_message = "*** Error: Could not parse the '%s' config file." % config.BT_CFG_PATHNAME
        try:
            parser = ConfigParser.SafeConfigParser()
            cfgs = parser.read(config.BT_CFG_PATHNAME)
        except ConfigParser.ParsingError as error:
            raise ValueError(error_message)
        section = 'general'
        editor_option = 'external_editor'
        start_line_option = 'start_at_line_arg'
        locale_option = 'locale'
        if not cfgs:
            # Default values
            parser.add_section(section)
            parser.set(section, editor_option, config.BT_EDITOR)
            parser.set(section, start_line_option, config.BT_EDITOR_START_LINE)
            parser.set(section, locale_option, config.BT_LOCALE)
            with open(config.BT_CFG_PATHNAME, 'wb') as configfile:
                parser.write(configfile)
            return
        try:
            config.BT_EDITOR = parser.get(section, editor_option)
            config.BT_LOCALE = parser.get(section, locale_option)
            config.BT_EDITOR_START_LINE = parser.get(section, start_line_option)
        except ConfigParser.Error:
            raise ValueError(error_message)



    def __init__(self, *args, **kwargs):
        # Check the working dirictory
        if not os.path.isdir(config.BT_PATH):
            os.makedirs(config.BT_PATH)
        # Open config file
        try:
            self.init_config()
        except ValueError, error:
            print(error)
            exit()
        # Shell history wrapper
        histfile = os.path.join(config.BT_PATH, ".history")
        try:
            readline.read_history_file(histfile)
            # default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
        # Set locale
        locale.setlocale(locale.LC_ALL, config.BT_LOCALE)
        # Init the database
        self.db = Database(config.BT_DB_PATHNAME)
        self.set_prompt()
        Cmd.__init__(self, args, kwargs)

    def emptyline(self):
        """Prevent a newline to use the last command"""
        pass

    def validate_alias(self, arg):
        """Parse and check the task"""
        # Check if task exists
        alias = helpers.parse_task_alias(arg)
        task = self.db.get_task_by_alias(alias['task'], alias['project'])
        if not task:
            raise ValueError(u"*** Error: The task '{}#{}' has not been "
                             "found.".format(alias['task'],
                                             alias['project']).encode('utf8'))
        return task

    def do_v(self, arg):
        """Shortcut for the about command"""
        self.do_about(arg)

    def do_about(self, arg):
        """Displays release information"""
        print("BloodyTracker V{version} ({rdate}){eol}"
              "Author: {author} ({email}){eol}".format(
                  eol=os.linesep, version=__version__, rdate=__release_date__,
                  author=__author__, email=__email__))

    def do_q(self, arg):
        """Shortcut for the exit command"""
        self.do_exit(arg)

    def do_quit(self, arg):
        """Alias for the exit command"""
        self.do_exit(arg)

    def do_exit(self, arg):
        """Exit from Bloody Tracker"""
        self.db.close_db()
        print(" \\o_  Bye-bye...")
        print(" /  ")
        print("<\\")
        sys.exit()

    def do_fill_db_with_fake_tracks(self, arg):
        """Fill with the test tasks"""
        print('*** Warning! All records will be deleted!')
        print('Do you really want to fill the Database with fake records? [y/N] ', end='')
        if not helpers.get_yes_no(default='n'):
            return
        self.db.fill()
        self.set_prompt()

    def create_project(self):
        """Creates a project"""
        # type(project_name) == unicode
        name = builtins.input('Name: ').decode('utf-8')
        try:
            cleaned = helpers.is_name_valid(name)
        except (ValueError, ), error:
            print(error)
            return
        description = builtins.input('Description: ').decode('utf-8')
        project = self.db.get_project_by_name(name)
        if project:
            print(u"*** Error: A project '%s' already exists." % name)
            return
        self.db.create_project(name, description)
        print(u"The project '%s' has been created." % name)
        self.set_prompt()

    def update_project(self, project_name):
        # type(project_name) == unicode
        project = self.db.get_project_by_name(project_name)
        if not project:
            print(u"*** Error: The project '{}' was not found."
                  "".format(project_name))
            return
        print('Do you want to update the project? [Y/n] ', end='')
        if not helpers.get_yes_no(default='y'):
            return
        name = helpers.prefill_input(
            'Name: ', empty_allowed=False,
            prefill=project['pname'].encode('utf8')).decode('utf8')
        description = helpers.prefill_input(
            'Description: ', empty_allowed=True,
            prefill=project['description'].encode('utf8')).decode('utf8')
        # validate the name
        checked = self.db.get_project_by_name(name)
        if checked and checked['pid'] != project['pid']:
            print(u"*** Error: A project '%s' already exists." % name)
            return
        self.db.update_project(project['pid'], name, description)
        print("The project has been updated.")
        self.set_prompt()

    def delete_project(self, project_name):
        """Delete the project and related task's and track's data"""
        # type(project_name) == unicode
        project = self.db.get_project_by_name(project_name)
        if not project:
            print(u"*** Error: The project '{}' was not found."
                  "".format(project_name))
            return
        print('Caution! The related tracking will be deleted as well.{eol}'
              'Do you really want to delete the project? [y/N] '
              ''.format(eol=os.linesep), end='')
        if not helpers.get_yes_no(default='n'):
            return
        self.db.delete_project_by_name(project_name)
        print(u"The project '%s' has been deleted." % project_name)
        self.set_prompt()

    def do_p(self, arg):
        """Shortcut of the 'project' command. Use 'help project' for details."""
        self.do_project(arg)

    def display_project_info(self, pname):
        """Displays project info"""
        project = self.db.get_project_by_name(pname)
        if not project:
            print(u"*** Error: The project '{}' has not been found."
                  "".format(pname))
            return
        timesheet_billed = self.db.get_timesheet(
            started='', finished=datetime.date.today(),
            group_by_mask=TS_GROUP_BY['project'],
            pname=project['pname'])
        timesheet_spent = self.db.get_timesheet(
            started='', finished=datetime.date.today(),
            group_by_mask=TS_GROUP_BY['project'],
            pname=project['pname'], only_billed=False)
        spent = helpers.seconds_to_human(
            timesheet_spent[0]['spent'] if timesheet_spent else 0)
        billed = helpers.seconds_to_human(
            timesheet_billed[0]['spent'] if timesheet_billed else 0)
        fields = ['Project: ', 'ID: ', 'Description: ',
                  'Time spent:', 'Time billed:']
        info = zip(fields, [project['pname'], project['pid'],
                            project['description'],
                            spent, billed])
        print(tabulate(info))

    def do_project(self, arg):
        """Command
    project -- project's related commands

Usage
    project <name> | <create>|<update>|<delete>

Description
    The command displays project information, creates a new project, updates and
    deletes one.

Parameters
    <name> - a name of the project
        Gets project's specific info - the id, name, description, spent and billed time.

    <create> ::= create
        Creates a new project.

    <update> ::= update <name>
        Updates project's info.

    <delete> ::= delete <name>
        Deletes a project. Related tasks and tracks will be deleted as well.
"""
        def _usage():
            self.do_help('project')
        args = shlex.split(arg)
        if not args:
            _usage()
            return
        commands = ['create', 'delete', 'update']
        first_arg = args[0].lower()
        is_project_info = first_arg not in commands
        if is_project_info:
            # Get the project info
            project_name = args[0].decode('utf8')
            self.display_project_info(project_name)
            return
        if first_arg == 'create':
            # Create a new project
            self.create_project()
            return
        if len(args) == 1:
            print(self.error_wrong_parameters)
            _usage()
            return
        project_name = args[1].decode('utf8')
        if first_arg == 'update':
            # Update a project
            self.update_project(project_name)
        elif first_arg == 'delete':
            # Delete a project
            self.delete_project(project_name)
        return

    # Task's commands
    def do_on(self, arg):
        """Command
    on -- start tracking a task

Usage
    on <alias>

Parameters
    <alias> ::= <task>#<project>"""
        # get the parsed alias
        try:
            alias = helpers.parse_task_alias(arg.decode('utf8'))
        except ValueError, error:
            print(error)
            return
        activity = self.db.get_active_task()
        if activity:
            print(u"*** Warning: There is an unfinished activity on the task "
                  u"'{task}#{project}' yet.{eol}"
                  u"    Please, close the task before start tracking the other."
                  u"".format(task=activity['tname'], project=activity['pname'],
                             eol=os.linesep))
            return
        # check if project exists
        project = self.db.get_project_by_name(alias['project'])
        if not project:
            print(u"*** Error: The project '{project}' has not been found. Please "
                  u"create one before the tracking will be started.".format(
                      project=alias['project']))
            return
        # Get Task
        task_id = self.db.get_task_or_create(alias['task'],
                                             project['pid'])
        # Create a new track
        track_id = self.db.create_track(task_id)
        self.set_prompt(u'{task}#{project}'.format(
            task=alias['task'], project=alias['project']).encode('utf-8'))
        print(u"You are on the task '%s#%s' now." % (alias['task'],
                                                     project['pname']))

    def do_d(self, arg):
        """Shortcut for the done an active task command. Use 'help done' for details."""
        self.do_done(arg)

    def do_done(self, arg):
        """Command
    done -- stop tracking an active task

Usage
    done"""
        task = self.db.get_active_task()
        if not task:
            print('There is not an active task.')
            return
        finished = self.db.finish_track(task[3])
        print(u"The task '{task}#{project}' has been done. Time was spent "
              "{activity}.".format(
                  task=task['tname'], project=task['pname'],
                  activity=helpers.seconds_to_human(
                      (finished - task['started']).total_seconds()))
             )
        self.set_prompt(self.bloody_prompt)

    def display_task_info(self, args):
        """Display task info"""
        # get the parsed alias
        try:
            task = self.validate_alias(args)
        except ValueError, msg:
            print(msg)
            return
        timesheet_billed = self.db.get_timesheet(
            started='', finished=datetime.date.today(),
            group_by_mask=TS_GROUP_BY['task'], tname=task['tname'],
            pname=task['pname'])
        timesheet_spent = self.db.get_timesheet(
            started='', finished=datetime.date.today(),
            group_by_mask=TS_GROUP_BY['task'], tname=task['tname'],
            pname=task['pname'], only_billed=False)
        spent = helpers.seconds_to_human(
            timesheet_spent[0]['spent'] if timesheet_spent else 0)
        billed = helpers.seconds_to_human(
            timesheet_billed[0]['spent'] if timesheet_billed else 0)
        fields = ['Task: ', 'Project: ', 'Description: ',
                  'Time spent:', 'Time billed:']
        info = zip(fields, [task['tname'], task['pname'],
                            task['description'],
                            spent, billed])
        print(tabulate(info))

    def update_task(self, args):
        try:
            task = self.validate_alias(args)
        except ValueError, msg:
            print(msg)
            return
        print('Do you want to update the task? [y/N] ', end='')
        if not helpers.get_yes_no(default='n'):
            return
        name = helpers.prefill_input(
            'Name: ', empty_allowed=False, prefill=task['tname'])
        description = helpers.prefill_input(
            'Description: ', empty_allowed=True, prefill=task['description'])
        # validate the name
        checked = self.db.get_task_by_alias(task['tname'], task['pname'])
        if checked and checked['tid'] != task['tid']:
            print("*** Error: A task with the name '%s' already exists in '%s' project." % (
                task['tname'], task['pname']))
            return
        self.db.update_task(task['tid'], name, description)
        print("The task has been updated.")
        self.set_prompt()

    def delete_task(self, args):
        """Delete the task and related track data"""
        try:
            task = self.validate_alias(args)
        except ValueError, msg:
            print(msg)
            return
        print('Caution! The related tracking will be deleted as well.{eol}'
              'Do you really want to delete the task? [y/N] '
              ''.format(eol=os.linesep))
        if not helpers.get_yes_no(default='n'):
            return
        self.db.delete_task(task['tid'])
        print("The task '%s' has been deleted ." % args)
        self.set_prompt()

    def do_t(self, arg):
        """Shortcut for the 'task' command. Use 'help task' for details."""
        self.do_task(arg)

    def do_task(self, arg):
        """Command
    task -- task's related commands.

Usage
    task <alias> | <udpate>|<delete>

Description
    The command displays general info, updates or deletes a task.

Parameters
    <alias>
        Gets task's specific info - the name, description, spent and billed time.

    <update> ::= update <alias>
        Updates the task's name and description.

    <delete> ::= delete <alias>
        Deletes the task and related tracks.

    <alias> ::= <task name>#<project name>

    """
        def _usage():
            self.do_help('task')
        args = arg.split()
        if not len(args):
            print(self.error_wrong_parameters)
            return
        commands = ['delete', 'update']
        first_arg = args[0].lower()
        if first_arg not in commands:
            # Display the task info
            self.display_task_info(first_arg.decode('utf-8'))
            return
        if len(args) == 1:
            print("*** Error: The task is not specified.")
            return
        if first_arg == 'update':
            self.update_task(args[1].decode('utf-8'))
            self.set_prompt()
        elif first_arg == 'delete':
            self.delete_task(args[1].decode('utf-8'))

    # Various Listing commands
    def do_pp(self, arg):
        """Lists of the projects. Use 'help projects' for details."""
        self.do_projects(arg)

    def do_projects(self, arg):
        """Command
    projects -- display a list of projects.

Usage
    projects [<period>]

Description
    Displays a list of projects for a date piriod. The command displays last
    10 projects unless the period is specified.

Period parameter
    <period> ::= <from> [<to>] | today|[d]week|[d]month|[d]year|all

    The date period can be specified by a single date, from-to pair or
    keyword - 'today', '[d]week', '[d]month', '[d]year', 'all'.

    'week', 'month', 'year' - The date keywords are periods beginning with
    the first calendar day of the period (e.g. 1st Aug, Monday or 1/1/2017).

    'dweek', 'dmonth', 'dyear' - periods having been begun 7, 31 or 365 days ago.

    <from>|<to> ::= <date>
    <date>      is national representation of the date. Take a look at the
                strftime('%x')."""

        args = shlex.split(arg)
        limit = 10
        from_date = to_date = ''
        if args:
            limit = 0
            try:
                from_date, to_date = helpers.parse_date_parameters(args)
            except ValueError, msg:
                print(msg)
                return
        projects = self.db.get_projects_with_activity_field(
            from_date, to_date, limit=limit)
        refined = map(lambda x: [
            x['pid'], x['name'],
            '[Active]' if x['active'] else '[closed]',
            datetime.datetime.strftime(x['created'], '%c').decode('utf8'),
            x['description']], projects)
        print(tabulate(refined, ['ID', 'Project', 'Activity', 'Created',
                                 'Description']))

    def do_tt(self, arg):
        """Shortcut of the list of tasks command. Use 'help tasks' for details."""
        self.do_tasks(arg)

    def do_tasks(self, arg):
        """Command
    tasks -- display a list of tasks.

Usage
    tasks [<period>]

Description
    Displays a list of tasks for a date piriod. The command displays last 10 tasks
    unless the period is specified.

Period parameter
    <period> ::= <from> [<to>] | today|[d]week|[d]month|[d]year|all

    The date period can be specified by a single date, from-to pair or
    keyword - 'today', '[d]week', '[d]month', '[d]year', 'all'.

    'week', 'month', 'year' - The date keywords are periods beginning with
    the first calendar day of the period (e.g. 1st Aug, Monday or 1/1/2017).

    'dweek', 'dmonth', 'dyear' - periods having been begun 7, 31 or 365 days ago.

    <from>|<to> ::= <date>
    <date>      is national representation of the date. Take a look at the
                strftime('%x')."""

        args = shlex.split(arg)
        if not args:
            # TODAY
            started = datetime.date.fromtimestamp(0)
            finished = datetime.date.today()
            limit = 10
        else:
            limit = 0
            try:
                started, finished = helpers.parse_date_parameters(args)
            except ValueError, err:
                print(err)
                return
        tasks = self.db.get_profiled_tasks(started, finished, limit)
        def _display_fields(task):
            return [
                task['tid'],
                u'{task}#{project}'.format(
                    task=task['tname'], project=task['pname']),
                u'{delta} / {started}'.format(
                    delta=helpers.timedelta_to_human(datetime.datetime.now() -
                                                     task['started']),
                    started=datetime.datetime.strftime(
                        task['started'], '%c').decode('utf8')
                    ) if not task['finished'] else '[closed]',
                task['description'].decode('utf8')
            ]
        refined = map(_display_fields, tasks)
        print(tabulate(refined, ['ID', 'Task', 'Activity', 'Description']))

    def do_a(self, arg):
        """Shortcut of the active task command. Use 'help active' for details."""
        self.do_active(arg)

    def do_active(self, arg):
        """Command
    active -- display an active task

Usage
    active

Description
    Display an active task if there is one."""
        task = self.db.get_active_task()
        if not task:
            print("There is not any active task yet.")
            return
        refined = [[
            task['tid'],
            '#'.join([task['tname'], task['pname']]),
            helpers.seconds_to_human(
                (datetime.datetime.now() - task['started']).total_seconds()),
            datetime.datetime.strftime(task['started'], '%c').decode('utf8'),
            task['description']
        ]]
        print(tabulate(refined, ['ID', 'Task', 'Activity',
                                 'Started at', 'Description']))

    def parse_track_line(self, line):
        """Parse a text line to get track's attributes"""
        try:
            # New track
            # groups - alias, started, finished
            groups = re.search(
                r'^\s*$|'
                r'^\s*(?P<is_billed>#*)'
                r'\s*(?P<task>\w+)#(?P<project>\w+)\s+'
                r'(?P<quote1>[\'"]{1})(?P<started>.*?)(?P=quote1)'
                r'\s+(?P<quote2>[\'"]{1})(?P<finished>.*?)(?P=quote2)'
                r'\s*$', line.decode('utf8'), re.U
            ).groupdict()
        except AttributeError:
            raise ValueError("*** Error: Unable to parse the line: '%s'" % line)
        return groups

    def parse_timesheet(self, lines, header_len):
        """Parse lines to dictionary"""
        data = []
        error_message = unicode(""
            "*** Error in line {n}: 'The task '{task}#{project}' containts "
            "an invalid period: '{started}'-'{finished}'.")
        for n, line in enumerate(lines):
            groups = self.parse_track_line(line)
            # ignore empty strings
            if not groups['task']:
                continue
            lnum = n + header_len + 2
            # Validate dates
            try:
                started = datetime.datetime.strptime(groups['started'], '%x %X')
                finished = datetime.datetime.strptime(groups['finished'], '%x %X')
            except ValueError, message:
                raise errors.ParsingError(error_message.format(
                    n=lnum, started=groups['started'], finished=groups['finished'],
                    task=groups['task'], project=groups['project']), lnum)
            if started > finished:
                raise errors.ParsingError(error_message.format(
                    n=lnum, started=started, finished=finished,
                    task=groups['task'], project=groups['project']), lnum)
            # Validate the task name
            task = self.db.get_task_by_alias(groups['task'], groups['project'])
            if not task:
                raise ValueError(u"*** Error in line {n}: The task '{t}#{p}' has not been "
                                "found.".format(n=lnum, t=groups['task'],
                                                p=groups['project']).encode('utf-8'))
            groups['started'] = started
            groups['finished'] = finished
            groups['tid'] = task['tid']
            data.append(groups)
        return data

    def create_tracks_contents(self, tracks):
        """Create a text body with tracks"""
        rows = []
        # Expose dates for an editor
        for track in tracks:
            rows.append([
                '%s%s' % (u'#  ' if not track['is_billed'] else '  ',
                          u'#'.join([track['tname'], track['pname']])
                          ),
                datetime.datetime.strftime(track['started'],
                                            "'%x %X'").decode('utf8'),
                datetime.datetime.strftime(track['finished'],
                                            "'%x %X'").decode('utf8')
            ])
        trows = tabulate(rows, ['Task', 'Started', 'Finished',
                                'Description'], tablefmt='simple')
        return trows

    def get_timesheet_header(self, started, finished):
        example = "cost#kafka '{time}' '{time}'".format(
            time=datetime.datetime.strftime(datetime.datetime.now(),
                                            "%x %X").decode('utf8')
        )
        contents = unicode(
            u"# From Date: {started}{eol}"
            u"# To Date:   {finished}{eol}"
            u"#{eol}"
            u"# Use the '#' character to mark the tracks as unbilled.{eol}"
            u'# Empty string will be ignore.{eol}'
            u'#{eol}'
            u"# Warning: Removing any track line causes the track record deletion!{eol}"
            u"#{eol}"
            u"# Example track:{eol}"
            u"#     {example}{eol}"
            u"#{eol}"
            u"{eol}".format(
                started=started,
                finished=finished,
                example=example,
                eol=os.linesep)
        ).encode('utf8')
        return contents

    def create_timesheet_contents(self, header, tracks):
        return "%s%s" % (header, tracks)

    def open_external_editor(self, contents, lnum=0):
        """Open an external editor with the contents"""
        with NamedTemporaryFile('w+', suffix=".tmp", delete=True) as tmp_file:
            tmp_file.write(contents)
            tmp_file.seek(0)
            # Run editor
            if config.BT_EDITOR_START_LINE:
                start_at_line_arg = "%s%s" % (config.BT_EDITOR_START_LINE, lnum)
            try:
                call([config.BT_EDITOR, start_at_line_arg, tmp_file.name])
            except OSError, msg:
                print("*** Error: %s Inspect the editor path '%s'."
                      "" % (config.BT_EDITOR, msg))
                raise
            # Fetch rows from file
            lines = tmp_file.readlines()
            return lines

    def update_timesheet(self, args):
        """Update timesheet with an external editor"""
        if len(args) == 1:
            print(self.error_wrong_parameters)
            return
        try:
            started, finished = helpers.parse_date_parameters(args[1:])
        except ValueError as error:
            print(error)
            return
        if started == datetime.date.fromtimestamp(0):
            track = self.db.get_minimal_started_track()
            if track:
                started = track['started']
            else:
                started = finished
        # Get timesheet records
        tracks = self.db.get_tracks_by_date(started, finished,
                                            also_unfinished=False)
        # Exposure tracks to the table
        tracks_contents = self.create_tracks_contents(tracks)
        lnum = 0
        header = self.get_timesheet_header(started, finished)
        header_length = len(header.split(os.linesep))
        while(True):
            try:
                # Create the editor's contents
                contents = self.create_timesheet_contents(header, tracks_contents)
                timesheet = self.open_external_editor(contents, lnum)
                # we must get the table header here due to the length of the columns
                table_header = timesheet[header_length-1:header_length+1]
                tracks = timesheet[header_length+1:]
            except OSError, message:
                print("*** Error: %s", message)
                return
            # Parse the input
            try:
                data = self.parse_timesheet(tracks, header_length)
            except errors.ParsingError as error:
                print(error.msg)
                print("Would you like to update the timesheet again? [Y/n] ")
                if not helpers.get_yes_no(default='y'):
                    return
                table_header.extend(tracks)
                tracks_contents = "".join(table_header)
                lnum = error.lnum
                continue
            break
        # Update the DB
        # TODO: get rid the danger operation
        self.db.delete_tracks_by_date(started=started, finished=finished)
        data.sort(key=operator.itemgetter('started'))
        for track in data:
            self.db.create_track(track['tid'],
                                 track['started'], track['finished'],
                                 int(not bool(track['is_billed'])))
        print('The timesheet has been updated.')

    def validate_object(self, keyword, thing):
        """Validate task/project object"""
        if keyword == 'task':
            # TASK
            task = self.validate_alias(thing)
            return task['tname'], task['pname']
        # PROJECT
        # check if project exists
        project = self.db.get_project_by_name(thing)
        if not project:
            raise ValueError("*** Error: The project '{project}' "
                             "has not been found.".format(
                                 project=thing.encode('utf-8')))
        return '', thing

    def get_report_parameters(self, args, default_mask=0):
        """Get report command's parameters"""
        # Get the task|project filter keyword and an alias
        pname = tname = ''
        mask = 0
        if args[0] in ('task', 'project'):
            if not len(args) >= 2:
                print("*** Error: Wrong format of the object parameter '%s'"
                      "" % args[0])
                return
            tname, pname = self.validate_object(
                keyword=args[0], thing=args[1].decode('utf-8'))
            args = args[2:]
        # Get 'extend' parameter
        if args and args[0] == 'extend':
            if len(args) == 1:
                print("*** Error: Wrong extend bitmask.")
                return
            # Get mask if 'extend' parameter presents
            mask = helpers.parse_extend_mask(args[1])
            args = args[2:]
        mask = default_mask if not mask else mask
        # Get dates
        started, finished = helpers.parse_date_parameters(args)
        return tname, pname, started, finished, mask

    def make_report(self, tname, pname, started, finished, mask):
        """Create a report"""
        timesheet = self.db.get_timesheet(started, finished, mask,
                                          tname=tname, pname=pname)
        headers = self.db.get_timesheet_fields(mask, get_headers=True)
        refined = []
        total_spent = 0
        if not timesheet:
            print("There are no tracks have been found.")
            return
        for row in timesheet:
            row = list(row)
            # Convert date/datetime types
            for i, column in enumerate(row):
                if type(column) is datetime.date:
                    row[i] = column.strftime('%x')
                elif type(column) is datetime.datetime:
                    row[i] = column.strftime('%x %X')
            # Convert spent time in seconds to a human readable string
            total_spent += row[-1]
            row[-1] = helpers.seconds_to_human(row[-1])
            refined.append(row)
        print(u"{eol}Date: {date}".format(
            eol=os.linesep, date=datetime.date.strftime(
                datetime.date.today(), "%a %b %d %Y").decode('utf8')))
        print(u"From: %s" % datetime.date.strftime(started, "%a %b %d %Y").decode('utf8'))
        print(u"To:   %s" % datetime.date.strftime(
            finished, "%a %b %d %Y").decode('utf8'))
        # add a total footer
        footer = [''] * len(headers)
        footer[0], footer[-1] = 'Total:', helpers.seconds_to_human(total_spent)
        refined.append(footer)
        # Footer workaround
        table = tabulate(refined, headers, tablefmt='psql',
                         stralign="right").split(os.linesep)
        table.insert(-2, table[2])
        print("{}".format(os.linesep).join(table))

    def report_timesheet(self, args):
        """Handle the report command"""
        if len(args) == 1:
            print(self.error_wrong_parameters)
            return
        # Shift 'report' keyword
        args = args[1:]
        pname = tname = ''
        mask = TS_GROUP_BY['date'] | TS_GROUP_BY['task']
        # Get report parameters
        try:
            tname, pname, started, finished, mask = \
               self.get_report_parameters(args, default_mask=mask)
        except ValueError, error:
            print(error)
            return
        if started == datetime.date.fromtimestamp(0):
            track = self.db.get_minimal_started_track(tname, pname)
            if not track:
                print("There are no tracks have been found.")
                return
            started = track['started']
        # Check if there is an unfinished task
        task = self.db.get_active_task(started, finished, tname, pname)
        if task:
            print(u"Warning: There is an unfinished task '{task}#{project}' "
                  "in the period from '{started}' to '{finished}'.{eol}"
                  "The unfinished record will be ignored.{eol}"
                  "Proceed creating the report? [Y/n] "
                  "".format(task=task['tname'], project=task['pname'],
                            started=datetime.date.strftime(
                                started, "%x").decode('utf8'),
                            finished=datetime.date.strftime(
                                finished, "%x").decode('utf8'),
                            eol=os.linesep), end='')
            if not helpers.get_yes_no(default='y'):
                return
        # Make a report
        self.make_report(tname, pname, started, finished, mask)

    def do_up(self, arg):
        """Update the timesheet. Look at 'help timesheet' for details."""
        self.do_timesheet('update %s' % arg)

    def do_upt(self, arg):
        """Update the timesheet for today. Look at 'help timesheet' for details."""
        self.do_timesheet('update today')

    def do_upw(self, arg):
        """Update the timesheet for a week. Look at 'help timesheet' for details."""
        self.do_timesheet('update week')

    def do_upm(self, arg):
        """Update the timesheet for a month. Look at 'help timesheet' for details."""
        self.do_timesheet('update week')

    def do_rt(self, arg):
        """Report the timesheet for today."""
        self.do_timesheet('report today')

    def do_rrt(self, arg):
        """Report the detailed timesheet for today."""
        self.do_timesheet('report extend track today')

    def do_rw(self, arg):
        """Report the timesheet for a week."""
        self.do_timesheet('report week')

    def do_rrw(self, arg):
        """Report the detailed timesheet for a week."""
        self.do_timesheet('report extend track week')

    def do_rm(self, arg):
        """Report the timesheet for a month."""
        self.do_timesheet('report month')

    def do_ry(self, arg):
        """Report the timesheet for a year."""
        self.do_timesheet('report year')

    def do_ts(self, arg):
        """A shortcut for the timesheet command. Take a look at 'help timesheet' for details."""
        self.do_timesheet(arg)

    def do_timesheet(self, arg):
        """Command
    timesheet -- timesheet's related commands

Usage
    timesheet <update> | <report>

Desciption
    Timesheet is a command manipulates a tracking data and creates a report.
    It updates tracks for a specified period, changes time was spent and may
    set a track as unbilled. A data of a report can be narrowed to fetch
    tracks for a certain task or project, combined and grouped by dates,
    projects, tracks and tasks using 'extend' parameter.

Parameters
    <update> ::= update <period>
            Update command allows update tracks by calling an external editor.
            Here you can change dates of tracks and comment any of ones
            to make them as unbilled.

            Use 'external_editor' option of config file to set up the editor.
            Make sure you run the editor in foreground.

    <report> ::= report [<object>] [<extend>] <period>
            Creates a timesheet report for the specified <object> (task or
            project) grouped by <extend> parameter. <Extend> parameter is
            a set of a keyword bitmask. Use <object> parameter to narrow a query.

            <object> ::= task <alias> | project <name>
                    Fetch tracks for a certain task or project.

            <alias> ::= <task name>#<project name>

            <extend> ::= [extend date|task|project|track]
                    Bitwise OR grouping keywords. If the parameter is omitted
                    the default value is date,task

Period parameter
    <period> ::= <from> [<to>] | today|[d]week|[d]month|[d]year|all

    The date period can be specified by a single date, from-to pair or
    keyword - 'today', '[d]week', '[d]month', '[d]year', 'all'.

    'week', 'month', 'year' - The date keywords are periods beginning with
    the first calendar day of the period (e.g. 1st Aug, Monday or 1/1/2017).

    'dweek', 'dmonth', 'dyear' - periods having been begun 7, 31 or 365 days ago.

    <from>|<to> ::= <date> | today
    <date>      is national representation of the date. Take a look at the
                strftime('%x')."""

        def _usage():
            self.do_help('timesheet')
        commands = ['update', 'report']
        words = shlex.split(arg)
        words = [token.lower() for token in words]
        if not len(words) or words[0] not in commands:
            print(self.error_wrong_parameters)
            return
        if words[0] == 'update':
            self.update_timesheet(words)
        elif words[0] == 'report':
            self.report_timesheet(words)
        return


def run():
    BTShell().cmdloop()

if __name__ == '__main__':
    run()
