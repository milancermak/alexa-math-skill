import os
import sys


os.environ['SKILL_TABLE_NAME'] = 'test-table'
os.environ['REGION'] = os.uname().nodename
os.environ['SERVICE'] = 'alexa-math-skill'
os.environ['STAGE'] = 'localtest'

# https://github.com/spulec/moto/issues/1793
# can go away once https://github.com/spulec/moto/pull/1952 is resolved
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'

# manipulating sys.path to make importing inside tests because ¯\_(ツ)_/¯
here = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(here, '..', 'src')) # for core
sys.path.insert(0, os.path.join(here, '..', 'src', 'functions', 'skill'))
