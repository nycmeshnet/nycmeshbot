import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    ACUITY_USER_ID = os.environ.get('ACUITY_USER_ID')
    ACUITY_API_KEY = os.environ.get('ACUITY_API_KEY')
    ACUITY_API_KEY = os.environ.get('ACUITY_API_KEY')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    #REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
