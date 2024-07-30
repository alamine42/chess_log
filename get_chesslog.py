import time
import calendar
import os
import shutil
import csv
import psycopg2
import logging
import argparse
import queries
import uuid
# import requests
import json

from chessdotcom import get_player_game_archives, get_player_games_by_month, get_player_stats, Client

from datetime import date, datetime, timedelta
from config import Config
from utils import enable_download_in_headless_chrome, db_connect

def locate_scores_files():
    """
    The scores file that gets downloaded has the date in the name, which means it's a different name every time it's downloaded.
    This function finds the file and returns the location.
    """

    path = os.getcwd()
    files = [i for i in os.listdir(path) if os.path.isfile(os.path.join(path,i)) and 'scores-' in i]
    if len(files) > 0:
        return files[0]
    else:
        return None

def get_list_of_workouts(start_dt, end_dt):
    """ 
    Call the SugarWOD Workouts API Endpoint to get workouts for a certain date range

    /workouts?dates={YYYYMMDD[-YYYYMMDD]}&track_id={TRACK_ID}

    Retrieve a list of Workouts. Optionally, filter by dates or track_id. 
    Dates can be a singular date_int or a range separated with a hyphen (7 day limit). 
    Default is "today". 

    Note that "today" on our server in the UTC time zone may be different than what you intended. 

    If no track_id is given, defaults to "all".

    """
    start_dt = start_dt.replace('-', '')
    end_dt = end_dt.replace('-', '')

    if start_dt == end_dt:
        date_query_str = '&dates=%s' % start_dt
    else:
        date_query_str = '&dates=%s-%s' % (start_dt, end_dt)

    logging.debug('Retrieving list of workouts from SugarWOD from %s to %s (inclusive) ...' % (start_dt, end_dt))
    workouts_url = Config.SUGARWOD_API_URL + \
        Config.SUGARWOD_WORKOUTS_ENDPOINT + \
        '?track_id=' + track_id + \
        date_query_str
    logging.debug('URL: %s' % workouts_url)

    sugarwod_workouts_list = []
    try:
        response = requests.get(workouts_url, data={'apiKey': Config.SUGARWOD_API_KEY})
        if response.status_code == 200:
            response_json = json.loads(response.text)

            for entry in response_json['data']:
                logging.debug(entry)
                if entry['attributes']['is_published'] == True:
                    workout = {}
                    workout['id'] = entry['id']
                    workout['date'] = str(entry['attributes']['scheduled_date_int'])
                    workout['title'] = entry['attributes']['title']
                    workout['description'] = entry['attributes']['description']
                    workout['score_type'] = entry['attributes']['score_type']
                    workout['results_link'] = entry['links']['ui_results']
                    workout['movement_ids'] = entry['attributes']['movement_ids']
                    sugarwod_workouts_list.append(workout)

    except Exception as e:
        logging.error(workouts_url)
        raise e

    return sugarwod_workouts_list

def get_list_of_athletes(workout_id):
    """ 
    Call the SugarWOD Workouts API Endpoint to get athletes for a certain workout

    /workouts/{workout_id}/athletes

    """
    logging.debug('Retrieving list of athletes from SugarWOD for workout %s ...' % workout_id)
    athletes_url = Config.SUGARWOD_API_URL + \
        Config.SUGARWOD_WORKOUTS_ENDPOINT + \
        '/' + workout_id + '/athletes'

    athletes_list = []
    while athletes_url is not None:
        try:
            response = requests.get(athletes_url, data={'apiKey': Config.SUGARWOD_API_KEY})
        except Exception as e:
            logging.error(athletes_url)
            raise e

        if response.status_code == 200:
            response_json = json.loads(response.text)
            logging.debug(response_json)
            for entry in response_json['data']:
                athlete = {}
                athlete['id'] = entry['id']
                athlete['first_name'] = entry['attributes']['first_name']
                athlete['last_name'] = entry['attributes']['last_name']
                athlete['email'] = entry['attributes']['email']
                athlete['gender'] = entry['attributes']['gender']
                athlete['profile_link'] = entry['links']['ui_athlete']
                athlete['workout_id'] = workout_id
                athletes_list.append(athlete)

        if 'next' in response_json['links']:
            athletes_url = response_json['links']['next']
        else:
            break

       
    return athletes_list

def load_workouts(cursor, workouts_list):

    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for workout in workouts_list:
        workout_data_str = '\',\''.join(
            [
                workout['id'],
                workout['date'],
                workout['title'],
                workout['description'],
                workout['score_type'],
                workout['results_link'],
                current_time_str
            ]
        )
        workout_data_str = "'" + workout_data_str + "'"

        # Delete the workout if it exists
        try:
            cursor.execute(queries.WORKOUT_DELETE_SQL % workout['id'])
        except Exception as e:
            logging.error('Error deleting workout!')
            raise e

        # Insert the workout
        try:
            cursor.execute(queries.WORKOUT_INSERT_SQL % (Config.SUGARWOD_WORKOUT_DATA_HEADER, workout_data_str))
        except Exception as e:
            logging.error('Error inserting workout!')
            raise e

def load_workout_athletes(cursor, workout_id, athletes_list):

    # Delete all athlete-workout mappings for this workout if they exist
    try:
        cursor.execute(queries.WORKOUT_ATHLETE_DELETE_SQL % workout_id)
    except Exception as e:
        logging.error('Error deleting workout!')
        raise e

    # Insert the athlete-workout mappings
    for athlete in athletes_list:
        workout_athlete_mapping_str = "'" + workout_id + "','" + athlete['id'] + "'"
        try:
            cursor.execute(queries.WORKOUT_ATHLETE_INSERT_SQL % (Config.SUGARWOD_WORKOUT_ATHLETE_DATA_HEADER, workout_athlete_mapping_str))
        except Exception as e:
            logging.error('Error inserting workout!')
            raise e

def main(download_only=False, reload_last=False, start_date='1999-01-01', end_date='1999-01-31', load_date='1999-01-31'):

    logging.info('----------------------------')
    logging.info('Chess Log - Chess Games Load')

    Client.request_config["headers"]["User-Agent"] = (
       "Chess Log App"
    )

    archives_response = get_player_game_archives(Config.CHESS_COM_USERNAME)

    list_of_months_in_archive = json.loads(archives_response.text)

    for month_url in list_of_months_in_archive['archives']:
        print(month_url)

    monthly_archive_response = get_player_games_by_month(Config.CHESS_COM_USERNAME, '2024', '7')

    list_of_games_json = json.loads(monthly_archive_response.text)

    # print(json.dumps(list_of_games_json, indent=4))
    # print(list_of_games_json)

    for game in list_of_games_json['games']:
        print(json.dumps(game, indent=4))
        break

    player_stats_response = get_player_stats(Config.CHESS_COM_USERNAME)
    player_stats_json = json.loads(player_stats_response.text)
    print(json.dumps(player_stats_json, indent=4))

    # conn = db_connect()
    # cur = conn.cursor()

    # logging.debug('Start %s, End %s, Load %s' % (data_start_dt, data_end_dt, data_load_dt))
    # latest_scores_filename = 'latest_scores.csv'
    
    # if not reload_last:
    #     os.remove(latest_scores_filename) if os.path.exists(latest_scores_filename) else logging.info('No scores file')

    #     logging.info('Fetching workout data ...')
    #     workouts_list = get_list_of_workouts(data_start_dt, data_end_dt)
    #     logging.info('Retrieved %d workouts ...' % len(workouts_list))

    #     logging.info('Loading workouts to database ...')
    #     load_workouts(cur, workouts_list)

    #     for workout in workouts_list:
    #         logging.debug(workout)
    #         logging.info('Fetching athlete & results data for workout %s ...' % workout['id'])
    #         athletes_list = get_list_of_athletes(workout['id'])
    #         logging.info('%d athletes logged a score for this workout!' % len(athletes_list))
    #         logging.debug('Loading athletes to database ...')
    #         load_workout_athletes(cur, workout['id'], athletes_list)

    #     # old_scores_filename = locate_scores_files()
    #     # if old_scores_filename is not None:
    #     #     logging.debug('Renaming downloaded file from %s to %s ...' % (old_scores_filename, latest_scores_filename))
    #     #     shutil.move(old_scores_filename, latest_scores_filename)

    # else:
    #     logging.info('Reloading last downloaded scores file ...')

    # conn.commit()
    # cur.close()
    # conn.close()

    logging.info('All done.')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='ChessLog ETL - Chess Games Loader!')
    parser.add_argument('-d', '--download_only', help='Download the file but do not load it into the DB.', action='store_true')
    parser.add_argument('-r', '--reload_last', help='Reload the last downloaded file', action='store_true')
    parser.add_argument('-p', '--print', action='store_true', help='Specifies logging to command line instead of file')
    parser.add_argument('-l', '--log_level', type=str, action='store', help='Log level (INFO, DEBUG, ERROR)', default='INFO')
    parser.add_argument('-s', '--start_date', type=str, action='store', help='Specify the scores start date (YYYY-MM-DD). Default is first day of last week.')
    parser.add_argument('-e', '--end_date', type=str, action='store', help='Specify the scores end date (YYYY-MM-DD). Default is today.')
    parser.add_argument('-t', '--load_date', type=str, action='store', 
        help='Specify the load date (YYYY-MM-DD) -- only use this for fixing historical loads. Make sure that load date partition doesnt already exist. Usage: python get_scores.py -s START_OF_BAD_DATA_MONTH -e END_OF_BAD_DATA_MONTH -t END_OF_BAD_DATA_MONTH', 
        default='1999-01-31')

    args = parser.parse_args()
    log_format = '%(levelname)s:%(asctime)s:%(message)s'

    if args.log_level == 'DEBUG':
        log_level = logging.DEBUG
    elif args.log_level == 'ERROR':
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    if args.print:
        logging.basicConfig(format=log_format, level=log_level)
    else:
        logging.basicConfig(format=log_format, level=log_level, filename=Config.LOG_FILE)

    main(download_only=args.download_only, reload_last=args.reload_last, start_date=args.start_date, end_date=args.end_date, load_date=args.load_date)
