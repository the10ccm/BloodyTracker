import os
import sqlite3
import random
import string
import time
import datetime
from datetime import timedelta
import operator

from tabulate import tabulate

import config


TS_GROUP_BY = dict(
    timestamp=0b10000,
    project=0b1000,
    task=0b0100,
    track=0b0010,
    date=0b0001
)


class Database:
    def init_db(self, db_path):
        self.conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES
        )
        self.conn.row_factory = sqlite3.Row
        self.conn.text_factory = lambda x: x.decode('utf8')
        #try:
        #except sqlite3.OperationalError:
        self.cursor = self.conn.cursor()

    def close_db(self):
        self.conn.close()

    def create_db(self):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        # Create Tables if do the not exist
        # PROJECTS
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS Projects('
            '   id INTEGER PRIMARY KEY, '
            '   customer_id INTEGER, '
            '   name VARCHAR UNIQUE COLLATE NOCASE, '
            '   description TEXT DEFAULT "", '
            '   created TIMESTAMP'
            ')')
        # TASKS
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS Tasks('
            '   id INTEGER PRIMARY KEY, '
            '   project_id INTEGER REFERENCES Projects(id) ON DELETE CASCADE, '
            '   name VARCHAR COLLATE NOCASE, '
            '   description TEXT DEFAULT ""'
            ')')
        # TRACKS
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS Tracks('
            '   id INTEGER PRIMARY KEY, '
            '   task_id INTEGER REFERENCES Tasks(id) ON DELETE CASCADE, '
            '   started TIMESTAMP, '
            '   finished TIMESTAMP, '
            '   is_billed INTEGER DEFAULT 1'
            ')')
        # CUSTOMERS
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS Customers('
                'id INTEGER PRIMARY KEY, '
                'name VARCHAR UNIQUE COLLATE NOCASE, '
                'description TEXT, '
                'created TIMESTAMP'
                ')')
        self.conn.commit()

    def __init__(self, db_name):
        # create DB
        self.init_db(db_name)
        self.create_db()

    def insert_test_task(self, project_id):
        name = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(3))
        self.cursor.execute(
            "insert into Tasks ('name', 'project_id') "
            "values('%s', '%s')" % (name, project_id)
            )
        self.conn.commit()
        return self.cursor.lastrowid

    def fill(self):
        """Fill with the test tasks"""
        self.cursor.execute('DELETE FROM Customers')
        self.cursor.execute('DELETE FROM Projects')
        self.cursor.execute('DELETE FROM Tasks')
        self.cursor.execute('DELETE FROM Tracks')
        # Add a Customer
        self.cursor.execute(
            "insert into Customers ('name', 'description') "
            "VALUES ('Andrey', 'Customer Numer One')")
        self.cursor.execute("SELECT * FROM Customers ORDER BY id LIMIT 1")
        customers = self.cursor.fetchone()
        #print('filled customers', customers)
        # Add a Project
        self.create_project('p1', 'Test Project #1')
        self.cursor.execute("SELECT * FROM Projects ORDER BY id LIMIT 1")
        project = self.cursor.fetchone()
        #print('filled projects', project)
        # Add the Task
        last_task = self.insert_test_task(project_id=1)
        # Add the Tracks
        started = datetime.datetime.now() - timedelta(days=4)
        self.create_track(last_task, started=started,
                          finished=started + timedelta(seconds=3601))
        self.create_track(last_task, started=started+timedelta(seconds=13600),
                          finished=started+timedelta(seconds=14600))
        self.create_track(last_task, started=started+timedelta(seconds=15600),
                          finished=started+timedelta(seconds=16600))

        last_task = self.insert_test_task(project_id=1)
        self.create_track(last_task, started=started+timedelta(seconds=17600),
                          finished=started+timedelta(seconds=18600))
        self.create_track(last_task, started=started+timedelta(seconds=19600),
                          finished=started+timedelta(seconds=20600))
        # Add a Project #2
        self.create_project('p2', 'Test Project #1')
        self.cursor.execute("SELECT * FROM Projects ORDER BY id LIMIT 1")
        project = self.cursor.fetchone()
        #print('filled projects', project)
        # Add the Task
        tasks = []
        last_task = self.insert_test_task(project_id=2)
        self.create_track(last_task, started=started+timedelta(seconds=21600),
                          finished=started+timedelta(seconds=22600))
        self.create_track(last_task, started=started+timedelta(seconds=23600),
                          finished=started+timedelta(seconds=24600))
        self.create_track(last_task, started=started+timedelta(seconds=25600),
                          finished=started+timedelta(seconds=26600))

        started = datetime.datetime.now() - timedelta(days=3)
        self.create_track(last_task, started=started,
                          finished=started + timedelta(seconds=3600))
        started = datetime.datetime.now() - timedelta(days=2)
        self.create_track(last_task, started=started,
                          finished=started + timedelta(seconds=3600))
        started = datetime.datetime.now() - timedelta(days=1)
        self.create_track(last_task, started=started,
                          finished=started + timedelta(seconds=3600))
        started = datetime.datetime.now() - timedelta(seconds=3300)
        self.create_track(last_task, started=started,
                          finished=started + timedelta(seconds=600))
        last_track = self.create_track(last_task)
        self.cursor.execute("SELECT * FROM Tracks ")
        tracks = self.cursor.fetchall()
        #print('filled tracks', tracks)
        print(tabulate(tracks, ['Track id', 'Task id', 'started', 'finished', 'billed'],
                       tablefmt='simple'))
        return

    # CUSTOMERS
    def get_customer(self, customer):
        self.cursor.execute(
            "SELECT id, name FROM Customers "
            "WHERE name == '{name:s}'".format(name=customer)
        )
        customer = self.cursor.fetchone()
        return customer

    def get_customer_or_create(self, customer):
        self.cursor.execute(
            "SELECT id, name FROM Customers "
            "WHERE name == '{name:s}'".format(name=customer)
        )
        customer = self.cursor.fetchone()
        if customer:
            return customer
        self.cursor.execute(
            "INSERT INTO Customers ('name')"
            "VALUES ('{name:s}')"
                .format(name=customer)
        )
        self.conn.commit()

    # PROJECTS
    def get_project_by_name(self, pname):
        self.cursor.execute(
            "SELECT "
            "   id as pid, name as pname, created as created, "
            "   description as description "
            "FROM Projects "
            "WHERE "
            "   Projects.name == ?", (pname.encode('utf8'),)
        )
        return self.cursor.fetchone()

    def update_project(self, pid, name, description):
        """Updates a project"""
        self.cursor.execute(
            "UPDATE Projects "
            "SET name=?, description=?"
            "WHERE id=?", (name.encode('utf8'), description.encode('utf8'),
                           pid)
        )
        self.conn.commit()

    def is_project_existent(self, pname, pid):
        """Checks if project already exists """
        self.cursor.execute(
            "SELECT "
            "   id as pid, name as name, created as created, "
            "   description as description "
            "FROM Projects "
            "WHERE "
            "   pid == '{pid}'"
            "   name == '{name}'".format(name=pname.encode('utf8'), pid=pid)
        )
        return self.cursor.fetchone()

    def get_projects_with_activity_field(self, from_date='', to_date='', limit=0):
        """Get list of project including a field is a project is finished"""
        where_clause = first_limit_clause = last_limit_clause = ''
        if limit:
            first_limit_clause = "SELECT * FROM ("
            last_limit_clause = " DESC LIMIT %d) ORDER BY pid ASC" % limit
        if from_date and to_date:
            where_clause = " AND DATE(Projects.created) BETWEEN '{from_date}' " \
                           "AND '{to_date}' ".format(from_date=from_date,
                                                     to_date=to_date)
        self.cursor.execute(
            "{first_limit_clause}"
            "SELECT "
            "   Projects.id as pid, Projects.name, Projects.created, "
            "   Projects.description, "
            "   SUM(CASE WHEN Tracks.finished == '' THEN 1 ELSE 0 end) AS active "
            "FROM Projects, Tracks, Tasks "
            "WHERE "
            "   Tasks.project_id == Projects.id AND "
            "   Tracks.task_id == Tasks.id {where_clause}"
            "GROUP BY Projects.id "
            "UNION SELECT "
            "   Projects.id as pid, Projects.name, Projects.created,"
            "   Projects.description, '' as active "
            "FROM Projects "
            "WHERE NOT EXISTS ("
            "   SELECT id FROM Tasks WHERE "
            "   Tasks.project_id == Projects.id "
            ") {where_clause}"
            "ORDER BY Projects.id {last_limit_clause}".format(
                where_clause=where_clause, first_limit_clause=first_limit_clause,
                last_limit_clause=last_limit_clause)
        )
        return self.cursor.fetchall()

    def create_project(self, pname, description=''):
        """Create a project"""
        self.cursor.execute(
            "INSERT INTO Projects ('name', 'description', created)"
            "VALUES (?, ?, ?)", (
                pname.encode('utf8'),
                description.encode('utf8'),
                str(datetime.datetime.now())
                )
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_project_or_create(self, pname):
        self.cursor.execute(
            "SELECT id, name FROM Projects "
            "WHERE name == '{name:s}'".format(name=pname.encode('utf8'))
        )
        project = self.cursor.fetchone()
        if project:
            return project
        return self.create_project(name)

    def delete_project_by_name(self, pname):
        self.cursor.execute(
            "DELETE FROM Projects WHERE name == '{name}'"
            "".format(name=pname.encode('utf8')))
        self.conn.commit()

    # TASKS
    def get_tasks(self, limit=10, add_activity=False):
        """Lists of last tasks"""
        activity_field = ''
        if add_activity:
            activity_field = ", SUM(CASE WHEN Tracks.finished == '' THEN 1 ELSE 0 END) "
        self.cursor.execute(
            "SELECT "
            "   Tasks.id, Tasks.name, Projects.id, Projects.name, "
            "   Tasks.description {activity_field}"
            "FROM Tasks, Projects, Tracks "
            "WHERE "
            "   Tasks.project_id == Projects.id AND "
            "   Tracks.task_id == Tasks.id "
            "GROUP BY Tasks.id "
            "ORDER BY Tasks.id DESC LIMIT {limit:d}".format(
            limit=limit, activity_field=activity_field)
        )
        tasks = self.cursor.fetchall()
        return tasks

    def get_profiled_tasks(self, started='', finished='', limit=0):
        """The list of last tasks between dates including unfinished"""
        where_clause = first_limit_clause = last_limit_clause = ''
        if started and finished:
            where_clause = str(
                "WHERE DATE(Tracks.started) BETWEEN '{started}' AND '{finished}'"
                "".format(started=started, finished=finished))
        if limit:
            first_limit_clause = "SELECT * FROM ("
            last_limit_clause = " DESC LIMIT %d) ORDER BY tid ASC" % limit

        self.cursor.execute(
            "{first_limit_clause}"
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.id as pid, "
            "   Projects.name as pname, Tasks.description as description, "
            "   Tracks.started as started, Tracks.finished as finished "
            "FROM Tasks, Projects, Tracks "
            "WHERE "
            "   Tasks.project_id == Projects.id AND "
            "   Tracks.task_id == Tasks.id AND "
            "   Tracks.id IN ("
            "       SELECT MAX(Tracks.id) FROM Tracks "
            "           {where_clause} "
            "       GROUP BY Tracks.task_id "
            "   ) ORDER BY tid {last_limit_clause}"
            "".format(
                where_clause=where_clause,
                first_limit_clause=first_limit_clause,
                last_limit_clause=last_limit_clause)
        )
        tasks = self.cursor.fetchall()
        return tasks

    def get_task_by_alias(self, tname, pname):
        """Get task by name"""
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.id as pid, "
            "   Projects.name as pname, Tasks.description as description "
            "FROM Tasks, Projects "
            "WHERE "
            "   Tasks.project_id == pid AND "
            "   tname == '{task:s}' AND "
            "   pname == '{project:s}'"
            "".format(task=tname.encode('utf8'), project=pname.encode('utf8'))
        )
        return self.cursor.fetchone()

    def create_task(self, name, pid):
        self.cursor.execute(
            "INSERT INTO Tasks ('name', 'project_id') "
            "VALUES "
            "   (?, ?)", (
                name.encode('utf8'),
                pid
            )
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_task_or_create(self, name, project_id):
        """Get a task or create one"""
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.id as pid, "
            "   Projects.name as pname, Tasks.description as description "
            "FROM Tasks, Projects "
            "WHERE "
            "   tname == '{task}' AND "
            "   Tasks.project_id == pid AND "
            "   pid == '{project!s}'"
            "".format(task=name.encode('utf8'), project=project_id)
        )
        last = self.cursor.fetchone()
        if last:
            return last['tid']
        return self.create_task(name, project_id)

    def _get_active_tasks(self):
        """Get active tasks"""
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.name as pname, "
            "   Tracks.id as track_id, Tracks.started as started, "
            "   Tracks.finished as finished, "
            "   Tasks.description as description "
            "FROM Tracks, Tasks, Projects "
            "WHERE "
            "   Tracks.task_id == Tasks.id AND "
            "   Tasks.project_id == Projects.id AND "
            "   finished == ''")
        return self.cursor.fetchall()

    def get_active_task(self, started='', finished='', tname='', pname=''):
        """Get an active task"""
        params = []
        where_date_clause = where_project_clause = where_task_clause = ''
        if tname:
            tname = tname.encode('utf8')
            where_task_clause = "tname == ? AND "
            params.append(tname)
        if pname:
            pname = pname.encode('utf8')
            where_project_clause = "pname == ? AND "
            params.append(pname)
        if started and finished:
            where_date_clause = "AND DATE(Tracks.started) " \
                                "   BETWEEN ? " \
                                "   AND ? "
            params.extend([started, finished])
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.name as pname, "
            "   Tracks.id as track_id, Tracks.started as started, "
            "   Tracks.finished as finished, "
            "   Tasks.description as description "
            "FROM Tracks, Tasks, Projects "
            "WHERE "
            "   {where_task_clause}"
            "   {where_project_clause}"
            "   Tracks.task_id == Tasks.id AND "
            "   Tasks.project_id == Projects.id AND "
            "   finished == '' "
            "   {where_date_clause}".format(
                    where_date_clause=where_date_clause,
                    where_project_clause=where_project_clause,
                    where_task_clause=where_task_clause
                ), params
            )
        return self.cursor.fetchone()

    def update_task(self, tid, name, description=''):
        """Updates the task info"""
        self.cursor.execute(
            "UPDATE Tasks "
            "SET name=?, description=?"
            "WHERE id=?", (
                name.encode('utf8'),
                description.encode('utf8'),
                tid
                )
        )
        self.conn.commit()

    def delete_task(self, tid):
        """"""
        self.cursor.execute(
            "DELETE FROM Tasks WHERE id == '{tid}'".format(tid=tid))
        self.conn.commit()

    # TRACKS
    def get_tracks_by_date(self, started='', finished='', also_unfinished=False):
        """Get tracks"""
        where_clause = ''
        between_clause = ''
        params = []
        if not also_unfinished:
            where_clause = "AND NOT finished == '' "
        if started and finished:
            between_clause = "AND DATE(started) BETWEEN ? AND ?"
            params.extend([started, finished])
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, "
            "   Projects.id as pid, Projects.name as pname, "
            "   Tracks.id as trid, Tracks.started as started, "
            "   Tracks.finished as finished, "
            "   Tracks.is_billed as is_billed "
            "FROM Tracks, Tasks, Projects "
            "WHERE "
            "   Tracks.task_id == tid AND "
            "   Tasks.project_id == pid"
            "   {where_clause} "
            "   {between_clause} "
            "ORDER BY Tracks.id".format(started=started,
                                        finished=finished,
                                        where_clause=where_clause,
                                        between_clause=between_clause),
            params
        )
        return self.cursor.fetchall()

    def get_track_by_id(self, tid):
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.name as pname, "
            "   Tracks.id as trid, Tracks.started as started, "
            "   Tracks.finished as finished, "
            "   Tracks.is_billed as is_billed "
            "FROM Tracks, Tasks, Projects "
            "WHERE "
            "   Tracks.task_id == tid AND "
            "   Tasks.project_id == Projects.id AND "
            "   trid == %d" % tid
        )
        return self.cursor.fetchone()

    def create_track(self, task_id, started='', finished='', is_billed=True):
        # started, finished - 9-item sequence, not float
        if not started:
            started = datetime.datetime.now()
        self.cursor.execute(
            "INSERT INTO Tracks "
            " ('task_id', 'started', 'finished', 'is_billed') "
            "VALUES (?, ?, ?, ?)", (task_id, started, finished, int(is_billed))
            )
        self.conn.commit()
        return self.cursor.lastrowid

    def finish_track(self, track_id, started=None):
        finished = datetime.datetime.now()
        if started and config.BT_TIMESHEET_ROUNDING and config.BT_ROUNDING_INCREMENT:
            delta = finished - started
            round_to = config.BT_ROUNDING_INCREMENT * 60
            seconds = round_to - delta.seconds % round_to
            finished = finished + datetime.timedelta(seconds=seconds)
        self.cursor.execute(
            "UPDATE Tracks SET finished=? WHERE id=?", (finished, track_id)
        )
        self.conn.commit()
        return finished

    def update_track(self, track_id, started, finished, is_billed):
        """Updates the time was spend and is billed flag of the track record"""
        self.cursor.execute(
            "UPDATE Tracks "
            "SET started=?, finished=?, is_billed=? "
            "WHERE id=?", (started, finished, is_billed, track_id)
        )
        self.conn.commit()

    def delete_tracks_by_date(self, started, finished, also_unfinished=False):
        """Deletes tracks by the date"""
        if not also_unfinished:
            where_clause = "AND NOT finished == '' "
        self.cursor.execute(
            "DELETE "
            "   FROM Tracks "
            "WHERE "
            "   DATE(started) BETWEEN ? AND ?"
            "   {where_clause}"
            "".format(where_clause=where_clause),
            (started, finished)
        )
        self.conn.commit()

    # TIMESHEET
    def get_group_by_clause(self, mask):
        """Makes a GROUP BY clause by bit mask"""
        def set_group_by_clause(bits, value, group_by):
            """Add a field to group_by clause"""
            if mask & bits:
                if group_by:
                    group_by = "%s," % group_by
                group_by = '{group_by} {value}'.format(group_by=group_by,
                                                       value=value)
            return group_by
        group_by = set_group_by_clause(TS_GROUP_BY['date'], 'DATE(started)', '')
        group_by = set_group_by_clause(TS_GROUP_BY['project'], 'Tasks.project_id',
                                       group_by)
        group_by = set_group_by_clause(TS_GROUP_BY['task'], 'Tracks.task_id',
                                       group_by)
        group_by = set_group_by_clause(TS_GROUP_BY['track'], 'Tracks.id', group_by)
        if group_by:
            group_by = "GROUP BY %s " % group_by
        return group_by

    def get_timesheet_fields(self, mask, get_headers=False):
        """Makes a list of ordered fields"""
        # Priority:
        #   datetime - 0
        #   date - 1
        #   task - 2
        #   project - 3
        #   spent - 4
        # date, tname, pname, started, finished, spent
        date_field = (0, 'DATE(started) as "date [date]"', 'Date')
        task_field = (1, 'tname', 'Task')
        project_field = (2, 'pname', 'Project')
        started_field = (3, 'DATETIME(started) as "started [timestamp]"', 'From')
        finished_field = (4, 'DATETIME(finished) as "finished [timestamp]"', 'To')
        spent_field = (5, 'spent', 'Time Spent')
        clause = set()
        if mask & TS_GROUP_BY['date']:
            clause.add(date_field)
        if mask & TS_GROUP_BY['task']:
            clause.update([task_field, project_field])
        if mask & TS_GROUP_BY['project']:
            clause.add(project_field)
        if mask & TS_GROUP_BY['track']:
            clause.update([task_field, project_field, started_field,
                           finished_field])
        clause.add(spent_field)
        to_get = 2 if get_headers else 1
        return map(operator.itemgetter(to_get),
                   sorted(clause, key=operator.itemgetter(0)))

    def get_timesheet_select_clause(self, mask):
        """Get prepared select's clause list of fields"""
        fields = self.get_timesheet_fields(mask)
        return ', '.join(fields)

    def get_minimal_started_track(self, tname='', pname=''):
        """Get a minimal tracked date"""
        params = []
        where_project_clause = where_task_clause = ''
        if tname:
            tname = tname.encode('utf8')
            where_task_clause = "tname == ? AND "
            params.append(tname)
        if pname:
            pname = pname.encode('utf8')
            where_project_clause = "pname == ? AND "
            params.append(pname)
        self.cursor.execute(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.name as pname, "
            "    DATE(started) as 'started [date]'"
            "FROM Tracks, Tasks, Projects "
            "WHERE "
            "   {where_task_clause}"
            "   {where_project_clause}"
            "   Tracks.task_id == tid AND "
            "   Tasks.project_id == Projects.id"
            "".format(where_task_clause=where_task_clause,
                      where_project_clause=where_project_clause), params)
        return self.cursor.fetchone()

    def get_timesheet(self, started, finished, group_by_mask, only_billed=True,
                      tname='', pname=''):
        """ Gets the time was spent for a task/project"""
        params = []
        only_billed_clause = where_project_clause = where_task_clause = ''
        if tname:
            params.append(tname.encode('utf8'))
            where_task_clause = "tname == ? AND "
        if pname:
            params.append(pname.encode('utf8'))
            where_project_clause = "pname == ? AND "
        if only_billed:
            only_billed_clause = " AND Tracks.is_billed == 1 "
        params.extend([started, finished])
        group_by_clause = self.get_group_by_clause(group_by_mask)
        query = str(
            "SELECT "
            "   Tasks.id as tid, Tasks.name as tname, Projects.name as pname, "
            "   SUM(STRFTIME('%s', finished)-STRFTIME('%s', started)) as spent,"
            "   Tracks.started as started, "
            "   Tracks.finished as finished "
            "FROM Tracks, Tasks, Projects "
            "WHERE "
            "   {where_task_clause}"
            "   {where_project_clause}"
            "   Tracks.task_id == tid AND "
            "   Tasks.project_id == Projects.id AND "
            "   ("
            "       DATE(started) BETWEEN ? AND ?"
            "       AND NOT Tracks.finished  == ''"
            "       {only_billed_clause}"
            "    ) "
            "{group_by_clause} "
            "ORDER BY started, Tasks.id"
            "".format(started=started, finished=finished,
                      where_task_clause=where_task_clause,
                      where_project_clause=where_project_clause,
                      group_by_clause=group_by_clause,
                      only_billed_clause=only_billed_clause)
        )
        #print(query)
        if group_by_mask:
            select_clause = self.get_timesheet_select_clause(group_by_mask)
            query = "SELECT {clause} FROM ({query})".format(
                query=query, clause=select_clause)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
