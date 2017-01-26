# -*- coding: utf_8 -*-

import os
import string
import random
import datetime
import unittest
from StringIO import StringIO
import random

from mock import patch

import config
import helpers
from database import Database
from bloodytracker import BTShell


class TestHelpers(unittest.TestCase):
    """Test helpers module"""
    def test_parse_extend_mask(self):
        mask = helpers.parse_extend_mask('date,project,task,track')
        self.assertEqual(mask, 0b1111)

    def test_parse_task_alias(self):
        tname = u'тикет'
        pname = u'проект'
        alias = helpers.parse_task_alias(u'{}#{}'.format(tname, pname))
        self.assertIn('task', alias)
        self.assertIn('project', alias)
        self.assertEqual(alias['task'], tname)
        self.assertEqual(alias['project'], pname)

    def test_parse_date(self):
        today = datetime.date.today()
        parsed = helpers.parse_date(today.strftime('%x'))
        self.assertEquals(today, parsed)
        with self.assertRaises(ValueError) as cm:
            helpers.parse_date('12/12-22')

    def test_parse_date_parameters(self):
        # Check if the parameters has one date
        today = datetime.date.today()
        res = helpers.parse_date_parameters((today.strftime('%x'),))
        self.assertEqual(res, (today, today))
        # Check if the parameters has two dates
        tomorrow = today + datetime.timedelta(days=1)
        res = helpers.parse_date_parameters((today.strftime('%x'),
                                             tomorrow.strftime('%x')))
        self.assertEqual(res, (today, tomorrow))
        # Check 'today|week|month|year|all' keywords
        res = helpers.parse_date_parameters(('today',))
        self.assertEqual(res, (today, today))
        res = helpers.parse_date_parameters(('week',))
        self.assertEqual(res, (today-datetime.timedelta(days=7), today))
        res = helpers.parse_date_parameters(('month',))
        self.assertEqual(res, (today-datetime.timedelta(days=31), today))
        res = helpers.parse_date_parameters(('year',))
        self.assertEqual(res, (today-datetime.timedelta(days=365), today))
        res = helpers.parse_date_parameters(('all',))
        self.assertTrue(res)


class TestCLITimesheet(unittest.TestCase):
    """Test shell commands"""
    def setUp(self):
        config.BT_DB_PATHNAME = ':memory:'
        self.shell = BTShell()
        self.unicode = True

    def test_timesheet(self):
        if self.unicode:
            pname1 = u'проект101'
            pname2 = u'проект201'
            tname1 = u'тикет101'
            tname21 = u'тикет201'
            tname22 = u'тикет202'
        else:
            pname1 = u'p101'
            pname2 = u'p201'
            tname1 = u't101'
            tname21 = u't201'
            tname22 = u't202'
        pid1 = self.shell.db.create_project(pname1)
        pid2 = self.shell.db.create_project(pname2)
        tid1 = self.shell.db.create_task(tname1, pid1)
        tid21 = self.shell.db.create_task(tname21, pid2)
        tid22 = self.shell.db.create_task(tname22, pid2)
        # Create tracks
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)
        yesterday = today - datetime.timedelta(days=1)

        # Warning! We should add some delta to 'started' field to get rid
        # an equel starting time for the all records
        def _create_track(tid, started, finished, dt=0):
            if not dt:
                dt = random.randint(1, 3600*12)
            delta = datetime.timedelta(seconds=dt)
            self.shell.db.create_track(tid, started+delta, finished+delta)
        # Yesterday
        # p1 t1: 70m
        # p2 t21: 1d 3h
        # Today
        # p1 t1: 40m, 30m, 15m
        # p2 t2.1: 50m
        # p2 t2.2: 2h:30m
        """
        External editor shot
        1  t1#p1   '01/24/2017 15:00:00'  '01/24/2017 16:10:00'
        2  t21#p2  '01/24/2017 15:15:00'  '01/25/2017 18:15:00'
        3  t1#p1   '01/25/2017 15:15:32'  '01/25/2017 15:55:32'
        4  t1#p1   '01/25/2017 16:15:00'  '01/25/2017 16:45:00'
        5  t1#p1   '01/25/2017 17:15:00'  '01/25/2017 17:30:00'
        6  t21#p2  '01/25/2017 18:00:00'  '01/25/2017 18:50:00'
        7  t22#p2  '01/25/2017 19:00:00'  '01/25/2017 21:30:00'
        Report all track screen
        |  Task | Project |              From |                To |        Time Spent |
        |    t1 |      p1 | 01/13/17 00:00:00 | 01/13/17 01:10:00 |        1h:10m:00s |
        |   t21 |      p2 | 01/13/17 00:00:00 | 01/14/17 03:00:00 | 1 days 3h:00m:00s |
        |    t1 |      p1 | 01/14/17 00:00:00 | 01/14/17 00:40:00 |        0h:40m:00s |
        |    t1 |      p1 | 01/14/17 00:00:00 | 01/14/17 00:30:00 |        0h:30m:00s |
        |    t1 |      p1 | 01/14/17 00:00:00 | 01/14/17 00:15:00 |        0h:15m:00s |
        |   t21 |      p2 | 01/14/17 00:00:00 | 01/14/17 00:50:00 |        0h:50m:00s |
        |   t22 |      p2 | 01/14/17 00:00:00 | 01/14/17 02:30:00 |        2h:30m:00s |
        """
        _create_track(tid1, yesterday,
                      yesterday+datetime.timedelta(seconds=70*60), 1)
        _create_track(tid21, yesterday,
                      yesterday+datetime.timedelta(days=1, seconds=3*3600), 2)
        _create_track(tid1, today, today+datetime.timedelta(seconds=40*60), 3)
        _create_track(tid1, today, today+datetime.timedelta(seconds=30*60), 4)
        _create_track(tid1, today, today+datetime.timedelta(seconds=15*60), 5)
        _create_track(tid21, today, today+datetime.timedelta(seconds=50*60), 6)
        finished = today+datetime.timedelta(seconds=2*3600+30*60)
        _create_track(tid22, today, finished, 7)
        # test today
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_timesheet('report  ')
            self.assertIn('Error', output.getvalue().strip())
        # test wrong date
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_timesheet('report project all')
            self.assertIn('Error', output.getvalue().strip())
        # test unknown project
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_timesheet('report project unknown_project all')
            self.assertIn('Error', output.getvalue().strip())
        # test wrong task
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_timesheet('report task %s all' % tname1.encode('utf8'))
            self.assertIn('Error', output.getvalue().strip())
        # test unknown task
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_timesheet('report task {}#unknown_project all'
                                    ''.format(tname1.encode('utf-8')))
            self.assertIn('Error', output.getvalue().strip())

        def _test_report(cmd, timesheet, total):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_timesheet(cmd)
                screened = output.getvalue().split(os.linesep)
                screen = screened[7:-4]
            self.assertEqual(len(timesheet), len(screen))
            for i, line in enumerate(screen):
                for assert_value in timesheet[i]:
                    self.assertIn(assert_value, line)
            self.assertIn(total, screened[-3])

        # test <default_extend> for <all>
        """
        |     Date |   Task |   Project |        Time Spent |
        | 01/12/17 |     t1 |        p1 |        1h:10m:00s |
        | 01/12/17 |    t21 |        p2 | 1 days 3h:00m:00s |
        | 01/13/17 |     t1 |        p1 |        1h:25m:00s |
        | 01/13/17 |    t21 |        p2 |        0h:50m:00s |
        | 01/13/17 |    t22 |        p2 |        2h:30m:00s |
        """
        timesheet = [
            (yesterday.strftime('%x'), tname1, pname1, '1h:10m:00s'),
            (yesterday.strftime('%x'), tname21, pname2, '1 days 3h:00m:00s'),
            (today.strftime('%x'), tname1, pname1, '1h:25m:00s'),
            (today.strftime('%x'), tname21, pname2, '0h:50m:00s'),
            (today.strftime('%x'), tname22, pname2, '2h:30m:00s')
        ]
        _test_report('report all', timesheet, '1 days 8h:55m:00s')

        # test extend <date, task> <a day>
        _test_report('report extend date,task all', timesheet, '1 days 8h:55m:00s')

        # test <default_extend> for <date,task> for <today>
        """
        |     Date |   Task |   Project |   Time Spent |
        | 01/14/17 |     t1 |        p1 |   1h:25m:00s |
        | 01/14/17 |    t21 |        p2 |   0h:50m:00s |
        | 01/14/17 |    t22 |        p2 |   2h:30m:00s |
        """
        timesheet = [
            (today.strftime('%x'), tname1, pname1, '1h:25m:00s'),
            (today.strftime('%x'), tname21, pname2, '0h:50m:00s'),
            (today.strftime('%x'), tname22, pname2, '2h:30m:00s')
        ]
        _test_report('report today', timesheet, '4h:45m:00s')

        # test <default_extend> for project p1
        """
        |     Date |   Task |   Project |   Time Spent |
        | 01/13/17 |     t1 |        p1 |   1h:10m:00s |
        | 01/14/17 |     t1 |        p1 |   1h:25m:00s |
        """
        timesheet = [
            (yesterday.strftime('%x'), tname1, pname1, '1h:10m:00s'),
            (today.strftime('%x'), tname1, pname1, '1h:25m:00s')
        ]
        _test_report('report project %s all' % pname1.encode('utf-8'),
                     timesheet, '2h:35m:00s')

        # test <default_extend> for task t1#p1
        """
        |     Date |   Task |   Project |        Time Spent |
        | 01/13/17 |    t21 |        p2 | 1 days 3h:00m:00s |
        | 01/14/17 |    t21 |        p2 |        0h:50m:00s |
        """
        timesheet = [
            (yesterday.strftime('%x'), tname21, pname2, '1 days 3h:00m:00s'),
            (today.strftime('%x'), tname21, pname2, '0h:50m:00s')
        ]
        _test_report('report task %s#%s all' % (
            tname21.encode('utf-8'),
            pname2.encode('utf-8')), timesheet, '1 days 3h:50m:00s')

        # test <extend> for <project>
        """
        |   Project |        Time Spent |
        |        p1 |        2h:35m:00s |
        |        p2 | 1 days 6h:20m:00s |
        """
        timesheet = [
            (pname1, '2h:35m:00s'),
            (pname2, '1 days 6h:20m:00s'),
        ]
        _test_report('report extend project all', timesheet, "1 days 8h:55m:00s")

        # test <extend> for <task>
        """
        |   Task |   Project |        Time Spent |
        |     t1 |        p1 |        2h:35m:00s |
        |    t21 |        p2 | 1 days 3h:50m:00s |
        |    t22 |        p2 |        2h:30m:00s |
        """
        timesheet = [
            (tname1, pname1, '2h:35m:00s'),
            (tname21, pname2, '1 days 3h:50m:00s'),
            (tname22, pname2, '2h:30m:00s')
        ]
        _test_report('report extend task all', timesheet, "1 days 8h:55m:00s")

        # test <extend> for <date>
        """
        |     Date |        Time Spent |
        | 01/13/17 | 1 days 4h:10m:00s |
        | 01/14/17 |        4h:45m:00s |
        """
        timesheet = [
            (yesterday.strftime('%x'), '1 days 4h:10m:00s'),
            (today.strftime('%x'), '4h:45m:00s'),
        ]
        _test_report('report extend date all', timesheet, '1 days 8h:55m:00s')

        # test <extend> for <date, project>
        """
        |     Date |   Project |        Time Spent |
        | 01/13/17 |        p1 |        1h:10m:00s |
        | 01/13/17 |        p2 | 1 days 3h:00m:00s |
        | 01/14/17 |        p1 |        1h:25m:00s |
        | 01/14/17 |        p2 |        3h:20m:00s |
        """
        timesheet = [
            (yesterday.strftime('%x'), pname1, '1h:10m:00s'),
            (yesterday.strftime('%x'), pname2, '1 days 3h:00m:00s'),
            (today.strftime('%x'), pname1, '1h:25m:00s'),
            (today.strftime('%x'), pname2, '3h:20m:00s'),
        ]
        _test_report('report extend date,project all', timesheet, '1 days 8h:55m:00s')
        # test <extend> for <track>
        """
        |   Task |   Project |              From |                To |        Time Spent |
        |     t1 |        p1 | 01/13/17 00:00:00 | 01/13/17 01:10:00 |        1h:10m:00s |
        |    t21 |        p2 | 01/13/17 00:00:00 | 01/14/17 03:00:00 | 1 days 3h:00m:00s |
        |     t1 |        p1 | 01/14/17 00:00:00 | 01/14/17 00:40:00 |        0h:40m:00s |
        |     t1 |        p1 | 01/14/17 00:00:00 | 01/14/17 00:30:00 |        0h:30m:00s |
        |     t1 |        p1 | 01/14/17 00:00:00 | 01/14/17 00:15:00 |        0h:15m:00s |
        |    t21 |        p2 | 01/14/17 00:00:00 | 01/14/17 00:50:00 |        0h:50m:00s |
        |    t22 |        p2 | 01/14/17 00:00:00 | 01/14/17 02:30:00 |        2h:30m:00s |
        """
        timesheet = [
            (tname1, pname1,
             (yesterday+datetime.timedelta(seconds=1)).strftime('%x %X'),
             (yesterday+datetime.timedelta(hours=1, minutes=10, seconds=1)
             ).strftime('%x %X'), "1h:10m:00s"),
            (tname21, pname2,
             (yesterday+datetime.timedelta(seconds=2)).strftime('%x %X'),
             (yesterday+datetime.timedelta(days=1, hours=3, minutes=0, seconds=2)
                ).strftime('%x %X'), "1 days 3h:00m:00s"),
            (tname1, pname1,
             (today+datetime.timedelta(seconds=3)).strftime('%x %X'),
             (today+datetime.timedelta(minutes=40, seconds=3)).strftime('%x %X'),
             "0h:40m:00s"),
            (tname1, pname1,
             (today+datetime.timedelta(seconds=4)).strftime('%x %X'),
             (today+datetime.timedelta(minutes=30, seconds=4)).strftime('%x %X'),
             "0h:30m:00s"),
            (tname1, pname1,
             (today+datetime.timedelta(seconds=5)).strftime('%x %X'),
             (today+datetime.timedelta(minutes=15, seconds=5)).strftime('%x %X'),
             "0h:15m:00s"),
            (tname21, pname2,
             (today+datetime.timedelta(seconds=6)).strftime('%x %X'),
             (today+datetime.timedelta(minutes=50, seconds=6)).strftime('%x %X'),
             "0h:50m:00s"),
            (tname22, pname2,
             (today+datetime.timedelta(seconds=7)).strftime('%x %X'),
             (today+datetime.timedelta(hours=2, minutes=30, seconds=7)
                ).strftime('%x %X'), "2h:30m:00s")
        ]
        _test_report('report extend track all', timesheet, '1 days 8h:55m:00s')


class TestCLIGeneral(unittest.TestCase):
    """Test shell commands"""
    def setUp(self):
        config.BT_DB_PATHNAME = ':memory:'
        #config.BT_DB_PATHNAME = 'xxx'
        self.shell = BTShell()

    def tearDown(self):
        pass

    def test_project_commands(self):
        """Test project commands"""
        # Test the wrong 'create' command
        with patch('builtins.input', return_value=''):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_project('create ')
                self.assertIn('Error', output.getvalue().strip())
        # Create a project
        name = u'проектp123'.encode('utf-8')
        project = self.shell.db.get_project_by_name(name.decode('utf-8'))
        self.assertFalse(project)
        with patch('builtins.input', return_value=name):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_project('create')
        project = self.shell.db.get_project_by_name(name.decode('utf-8'))
        self.assertTrue(project)
        self.assertEqual(project['pname'], name.decode('utf-8'))
        # Update a project
        new_name = u'юникодM321'
        with patch('helpers.get_yes_no', return_value=True):
            with patch('sys.stdout', new=StringIO()) as output:
                with patch('builtins.input', new=lambda _: new_name.encode('utf-8')):
                    self.shell.do_project('update %s' % name)
        self.assertIn('has been updated', output.getvalue().strip())
        updated_project = self.shell.db.get_project_by_name(new_name)
        self.assertEqual(updated_project['pid'], project['pid'])
        self.assertEqual(updated_project['pname'], new_name)
        self.assertEqual(updated_project['description'], new_name)
        # Test 'delete' command
        name = new_name
        with patch('helpers.get_yes_no', return_value=True):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_project('delete %s' % name.encode('utf-8'))
        project = self.shell.db.get_project_by_name(name)
        self.assertFalse(project)

    def test_task_actions(self):
        """Test on, done, delete, info commands"""
        task = u'тикет321'.encode('utf-8')
        project = u'проект99'.encode('utf-8')
        # check wrong task format
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_on('{}'.format(task))
            self.assertIn('Wrong', output.getvalue().strip())
        # check an unknown task format
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_on('{}#{}'.format(task, project))
            self.assertIn(u'not been found', output.getvalue().strip())
        # Create project
        with patch('builtins.input', return_value=project):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_project('create')
        # Done a non-existent task
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_done('')
            self.assertIn('There is not', output.getvalue().strip())
        # Create a task
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_on('{}#{}'.format(task, project))
            self.assertIn('You are', output.getvalue().strip())
        # Done the task
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_done('')
            self.assertIn('has been done', output.getvalue().strip())
        # Get the task info
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_task(task)
            self.assertIn('Error', output.getvalue().strip())
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_task('%s#%s' % (task, project))
            self.assertIn('Time spent', output.getvalue().strip())
        # Delete the task
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_task('delete %s' % task)
            self.assertIn('Error', output.getvalue().strip())
        with patch('helpers.get_yes_no', new=lambda default: True):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_task('delete xxx#zzz')
                self.assertIn('not been found', output.getvalue().strip())
        with patch('helpers.get_yes_no', new=lambda default: True):
            with patch('sys.stdout', new=StringIO()) as output:
                self.shell.do_task('delete {}#{}'.format(task, project))
                self.assertIn('has been deleted', output.getvalue().strip())

    def test_list_of_projects(self):
        """Test how lists are displayed"""
        def _create_project():
            name = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(5))
            with patch('sys.stdout', new=StringIO()) as output:
                with patch('builtins.input', return_value=name):
                    self.shell.do_project('create')
            return name
        projects = [_create_project() for p in range(12)]
        self.assertEqual(len(projects), 12)
        # Check the list of last 10 projects
        with patch('sys.stdout', new=StringIO()) as output:
            self.shell.do_projects('')
            screen = output.getvalue().strip()
        for pname in projects[-10:]:
            self.assertIn(pname, screen)
        for pname in projects[0:2]:
            self.assertNotIn(pname, screen)
        # Check date parameters
        with patch('sys.stdout', new=StringIO()) as output:
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            self.shell.do_projects("%s %s" % (yesterday.strftime('%x'),
                                              today.strftime('%x')))
            screen = output.getvalue().strip()
        for pname in projects:
            self.assertIn(pname, screen)


if __name__ == '__main__':
    unittest.main()
