import os


home_dir = os.path.expanduser("~")

BT_PATH = os.path.join(home_dir, '.bloodytracker')
BT_DB_FILENAME = 'bt.db'
BT_DB_PATHNAME = os.path.join(BT_PATH, BT_DB_FILENAME)
BT_CFG_FILENAME = 'bt.cfg'
BT_CFG_PATHNAME = os.path.join(BT_PATH, BT_CFG_FILENAME)

BT_EDITOR = 'vim'
BT_EDITOR_START_LINE = '+'
# use 'locale -a' command in a shell to get a list of available locales
BT_LOCALE = 'en_US'