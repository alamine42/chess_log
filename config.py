import os
import sys
import json
from pprint import pprint

basedir = os.path.abspath(os.path.dirname(__file__))

if os.path.exists('config.env'):
    # print('Importing environment from .env file')
    for line in open('config.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1].replace("\"", "")

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
    SLACK_WEBHOOK_TEST_URL = os.environ.get('SLACK_WEBHOOK_TEST_URL')
    LOG_FILE = 'sugarwod_etl.log'
    SUGARWOD_URL = 'https://app.sugarwod.com/login'
    SUGARWOD_CALENDAR_URL = 'https://app.sugarwod.com/workouts/calendar?track=workout-of-the-day'
    SUGARWOD_USER = 'mehdi@brazenfitness.com'
    SUGARWOD_PASS = os.environ.get('SUGARWOD_PASS')
    SUGARWOD_API_KEY = os.environ.get('SUGARWOD_API_KEY')
    SUGARWOD_API_URL = 'https://api.sugarwod.com/v2'
    SUGARWOD_WORKOUTS_ENDPOINT = '/workouts'
    SUGARWOD_ATHLETES_ENDPOINT = '/athletes'
    SUGARWOD_WOTW_TRACK_ID = 'G20JYmUckd'
    SUGARWOD_THRESHOLD_DAYS = 60
    SUGARWOD_WORKOUT_DATA_HEADER = 'workout_id, workout_date, workout_title, workout_description, score_type, results_link, last_update'
    SUGARWOD_WORKOUT_ATHLETE_DATA_HEADER = 'workout_id, athlete_id'
    SUGARWOD_ATHLETE_DATA_HEADER = 'athlete_id, first_name, last_name, email, gender, profile_link, is_active, last_update'


class MailchimpConfig(object):
    MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY')
    MAILCHIMP_SERVER = os.environ.get('MAILCHIMP_SERVER')
    MAILCHIMP_LIST_ID = os.environ.get('MAILCHIMP_LIST_ID')
    MAILCHIMP_MEMBER_SEGMENT_ID = os.environ.get('MAILCHIMP_MEMBER_SEGMENT_ID')
    MAILCHIMP_TAGS = {
        'exmember': 'journey:ex-member',
        'member': 'journey:member',
        'lead': 'journey:lead',
        'onramp': 'journey:onramp'
    }
    LOG_FILE = 'brzn_etl_mailchimp.log'

class MailgunConfig(object):
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = 'mail.brazenfitness.com'
    MAILGUN_SENDER = 'Brazen Fitness <info@brazenfitness.com>'
    MAILGUN_SENDMSG_ENDPOINT = 'https://api.mailgun.net/v3/mail.brazenfitness.com/messages'

class PostgresConfig(object):
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
