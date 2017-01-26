```
▄▄▄▄· ▄▄▌              ·▄▄▄▄   ▄· ▄▌    ▄▄▄▄▄▄▄▄   ▄▄▄·  ▄▄· ▄ •▄ ▄▄▄ .▄▄▄  
▐█ ▀█▪██•  ▪     ▪     ██▪ ██ ▐█▪██▌    •██  ▀▄ █·▐█ ▀█ ▐█ ▌▪█▌▄▌▪▀▄.▀·▀▄ █·
▐█▀▀█▄██▪   ▄█▀▄  ▄█▀▄ ▐█· ▐█▌▐█▌▐█▪     ▐█.▪▐▀▀▄ ▄█▀▀█ ██ ▄▄▐▀▀▄·▐▀▀▪▄▐▀▀▄
██▄▪▐█▐█▌▐▌▐█▌.▐▌▐█▌.▐▌██. ██  ▐█▀·.     ▐█▌·▐█•█▌▐█ ▪▐▌▐███▌▐█.█▌▐█▄▄▌▐█•█▌
·▀▀▀▀ .▀▀▀  ▀█▄▀▪ ▀█▄▀▪▀▀▀▀▀•   ▀ •      ▀▀▀ .▀  ▀ ▀  ▀ ·▀▀▀ ·▀  ▀ ▀▀▀ .▀  ▀
```

Bloody Tracker is a console time tracker. The tracker allows you to track tasks, inspect how much time was spent, manipulate tracking data and create a summary about working hours.


## Installation

Just get the repo and install one:
```
git clone https://github.com/the10ccm/BloodyTracker
cd bloodytracker
python setup.py install
```
Even you can do this by executing:
```
pip install git+git://github.com/the10ccm/BloodyTracker.git
```

## Configuration

The same as working files, the configuration file `bt.cfg` is located in the home directory `{$HOME}/.bloodytracker/`. The config file is being created automatically after the tracker was run unless the file was not found.

There are some useful options that can help you to tickle the tracker.
```
# use 'locale -a' command in a shell to get a list of available locales
locale='en_US'

# set an external editor that can work in foreground
external_editor='vim'
```


## Usage

After the installation you can run the tracker:
```
bloodytracker
```

### Quick Start

To make a long story short, here is a typical scenario:

1) Create a project:
```
(bloody)> project create
Name: quickstart
Description: We are there
The project 'quickstart' has been created.
(bloody)>
```
2) Start tracking a task:
```
(bloody)> on run#quickstart
You are on the task 'run#quickstart' now.
(run#quickstart)>
```
3) Stop tracking the task:
```
(run#quickstart)> done
The task 'run#quickstart' has been done. Time was spent 0h:02m:43s.
(bloody)>
```
4) Inspect how much time was spent today:
```
(bloody)> timesheet report today

Date: 01/23/2017
From: 01/23/2017
To:   01/23/2017
+------------+--------+------------+--------------+
|       Date |   Task |    Project |   Time Spent |
|------------+--------+------------+--------------|
| 01/23/2017 |    run | quickstart |   0h:02m:44s |
|------------+--------+------------+--------------|
|     Total: |        |            |   0h:02m:44s |
+------------+--------+------------+--------------+
(bloody)>
```
5) Quit the tracker:
```
(bloody)> quit
 \o_  Bye-bye...
 /  
<\
```
That's all!

> **Note:**
The `(bloody)` prompt is being exchanged by current `(run#quickstart)` task name and vice versa.

### Project facilities

Project management is realized by a `project` command. The command allows to get information, create a new project, update and delete one. Usage:
```
project <command>
```

where the `<command>` is:
- `<name>`  - get project's specific info: general info, spent/billed time.
- `update <name>`  - update a project
- `delete <name>`  - delete a task

> **Note:**
Over deletion the related tasks and tracks will be deleted as well.


### Tracking

You don't need to create a task before start tracking it. Moreover, there is no an ability to create the new task but just start tracking one.
The start tracking command syntax is:
```
on <task>#<project>
```

> **Note:**
A task is ever pointed by a tuple of task and project names. The names are case-insensitive!

Stop tracking is extremely straight-forward. Just do it:
```
done
```

### Task management
Task management is realized by a `task` command and similar to the project facilities. The syntax is:
```
task <command>
```

where the `<command>` is:
- `<name>`    - get task's info by name: general info, spent/billed time.
- `update`    - update a task
- `delete`    - delete a task

> **Note:**
As well as in the project case, if a task is being deleted, related tracking records are being deleted as well.

### Inspection

Bloody tracker provides some useful commands that allow to keep you informed about what is happening. Here they are:
- `projects` - display a list of projects and their activities for a date period
- `tasks`    - display a list of tasks and their activities for a date period
- `active`   - display statistic of an active task if there is one.

#### Projects and Tasks
The syntax of the `projects` and `tasks` commands is:
```
<command> [<period>]
```

The commands display last 10 project/tasks unless the period parameter is omitted. The list contains the general fields such as: an ID, task and project names, description. As well there is an `Activity` field which exposes the state of a task or project. The state is marked as `[closed]` if a task is done and a project is not active. In a case, if the task is being tracked, the activity field shows how much time already was spent since tracking was started.

Here is a shot of using this commands:
```
(killem#pitlane)> projects
  ID  Project    Activity    Created                   Description
----  ---------  ----------  ------------------------  -----------------
   3  Fastlane   [closed]    Mon Jan 23 22:27:24 2017  We are here
   4  pitlane    [Active]    Tue Jan 24 14:46:37 2017  Backstage project
(killem#pitlane)> tasks
  ID  Task            Activity                               Description
----  --------------  -------------------------------------  -------------
   4  run#Fastlane    [closed]
   5  killem#pitlane  0h:28m:02s / Tue Jan 24 14:47:37 2017
(killem#pitlane)>
```

#### Period parameter
The period parameter has its own syntax:
```
[<from> [<to>]] | [today|week|month|year|all]
```
The date period can be specified by a single date, from-to pair or keywords: `today`, `week`, `month`, `year`, `all`.

The dates have national representation of the date. Take a look at the `strftime('%x')` function or run `date "+%x"` in the shell. The representation of the date depends on the `locale` option in the config. So you can fiddle one to what you want to see and how you want to input dates.

#### Active Task
To get information about current active task use the command:
```
active
```
It displays the same information as the commands above but only if an active task was found.
Example:
```
(t1#p1)> active
  ID  Task    Activity    Started at                Description
----  ------  ----------  ------------------------  -------------
   1  t1#p1   0h:40m:23s  Thu Jan 26 13:35:27 2017  Bake a cake
(t1#p1)>
```

## Timesheet
Timesheet is a command manipulates tracking data and creates a report. Using an external editor, it allows to update tracks for a specified period, change how much time must be spent and mark any tracks as unbilled. So now we will focus on two actions: updating and reporting.

### How to update tracking data
Update command allows to update tracks in an external editor where you can change working hourse and mark any tracks to make them unbilled by the '#' character. Use the 'external_editor' config option to set up the editor. Make sure the editor can be run in foreground.

The syntax of the update command is:
```
timesheet update <period>
```
> **Note:**
The `<period>` parameter has [general format](#period-parameter). It is already descriped above for the `tasks` and `projects` commands

Example:
```
(bloody)> timesheet update all

# From Date: 2017-01-01
# To Date:   2017-01-24
#
# Update the dates only!
# Use the '#' character to mark a track as unbilled.

  ID  Task          Started                Finished
----  ------------  ---------------------  ---------------------
  14  run#Fastlane  '01/23/2017 22:28:09'  '01/23/2017 22:30:53'
  15  run#Fastlane  '01/24/2017 00:28:23'  '01/24/2017 00:50:19'
#  16  run#Fastlane  '01/24/2017 00:50:36'  '01/24/2017 00:50:38'
  17  run#Fastlane  '01/24/2017 14:40:15'  '01/24/2017 14:47:10'
```

### Timesheet Report
At the end we have come to the moment for what this whole thing is all about. It is how to make Bloody Tracker get a summary of working hours. The summary is presented in a tabular form. The tracker manages various essential entities. There are only four entities: a *date*, *project*, *task* and *track record*. Every one of such entities maps a set of certain track fields or whole row records to a column in the result table. The result set is grouped according to the purpose of the entity was used. What does it mean? It means when the *date* entity is used the total is reckoned for a set of tracking records grouped by the date field. The result table will contain only those columns that were specified by the entities.

Let's go through the the syntax of the report command:
```
timesheet report [<object>] [<extend>] <period>
```
The first parameter is `<object>`. Here we can set a certain task or project that we want to fetch track records for. The format of the parameter is:
```
task <task>#<project> | project <name>
```
The `<extend>` parameter obliges the final report table to use only those entities that were listed. The syntax is:
```
extend date|task|project|track
```
Bloody tracker uses nothing but entities that were listed. However if the `<extend>` parameter is omitted the tracker uses the `date|task` mask by default.

The entities can be mixed as a bitwise OR mask. The entities are represented in the table according to their priory:
```Date > Task > Project > Track```

> **Note:**
The `task` entity always adds the `Task` and `Project` columns to the final table, however track records will be grouped only by the `Task` field.

There are some examples.
- To get working hours by a date for a month
```
(bloody)> timesheet report extend date month

Date: 01/26/2017
From: 01/24/2017
To:   01/26/2017
+------------+-------------------+
|       Date |        Time Spent |
|------------+-------------------|
| 01/24/2017 | 1 days 4h:10m:00s |
| 01/25/2017 |        4h:45m:00s |
| 01/26/2017 |        0h:14m:29s |
|------------+-------------------|
|     Total: | 1 days 9h:09m:29s |
+------------+-------------------+
```

- To get working hours by a project for a whole time period
```
(bloody)> timesheet report extend date,project all

Date: 01/26/2017
From: 01/24/2017
To:   01/26/2017
+------------+-----------+-------------------+
|       Date |   Project |        Time Spent |
|------------+-----------+-------------------|
| 01/24/2017 |        p1 |        1h:10m:00s |
| 01/24/2017 |        p2 | 1 days 3h:00m:00s |
| 01/25/2017 |        p1 |        1h:25m:00s |
| 01/25/2017 |        p2 |        3h:20m:00s |
| 01/26/2017 |        p1 |        0h:14m:29s |
|------------+-----------+-------------------|
|     Total: |           | 1 days 9h:09m:29s |
+------------+-----------+-------------------+
```

- To get working hours by a date and task for a week
```
(bloody)> timesheet report week

Date: 01/26/2017
From: 01/19/2017
To:   01/26/2017
+------------+--------+-----------+-------------------+
|       Date |   Task |   Project |        Time Spent |
|------------+--------+-----------+-------------------|
| 01/24/2017 |     t1 |        p1 |        1h:10m:00s |
| 01/24/2017 |    t21 |        p2 | 1 days 3h:00m:00s |
| 01/25/2017 |     t1 |        p1 |        1h:25m:00s |
| 01/25/2017 |    t21 |        p2 |        0h:50m:00s |
| 01/25/2017 |    t22 |        p2 |        2h:30m:00s |
| 01/26/2017 |     t1 |        p1 |        0h:14m:29s |
|------------+--------+-----------+-------------------|
|     Total: |        |           | 1 days 9h:09m:29s |
+------------+--------+-----------+-------------------+
```

### Shortcuts
Bloody Tracker provides an ability to shortcut the commands. Here they are:
```
a     - active
d     - done
pp    - projects
p     - project
tt    - tasks
t     - task
ts    - timesheet
tsup  - timesheet update today
q     - quit
```

#### Author: Andrey Aleksandrov (the10ccm@gmail.com) (c) 2017