#!/usr/bin/env python3.5
#####################################
#    LAST UPDATED     28 AUG 2016   #
#####################################
"""
Gets US soccer matches and updates the sidebar
"""
import json
import re
from time import sleep
import traceback
import logging
import logging.handlers
import os
import datetime
import requests
import praw


def get_importio(link):
    """
    Given an importio link, returns the json data
    :param link: Importio link
    :return: JSON that the importio link yields
    """
    url = requests.get(link).text
    return json.loads(url)


def push(text, details, r):
    """
    Push a message to computer
    :param text: MNT or WNT
    :param details: Match details
    :param r: PRAW instance
    :return: None
    """
    try:
        from pushbullet import Pushbullet
        with open('token.txt') as files:
            token = files.read().strip()
        pb = Pushbullet(token)
        lst = text.split('?')
        pb.push_note('{} match today at {} on {}'.format(details, lst[4], lst[3]),
                     '', device=pb.get_device('Computer'))
    except ImportError:
        lst = text.split('?')
        r.send_message('RedRavens', '{} Match Today'.format(details),
                       '{} match today at {} on {}'.format(details, lst[4], lst[3]))


def fix_venue(venue):
    """
    Fixes stadia information
    :param venue: String of a stadium, city, country/state
    :return: String of city, or @country if away
    """
    venue = venue.replace("Match Guide", "").strip()
    countries = ['Netherlands', 'England', 'Chile', 'Sweden',
                 'Canada', 'Denmark', 'France',
                 'Costa Rica', 'Honduras', 'Mexico', 'Switzerland',
                 'Cyprus', 'New Zealand', 'Germany',
                 'Serbia', 'Brazil', 'Trinidad & Tobago', 'Colombia',
                 'Guatemala', 'Jamaica', 'Grenada',
                 'Croatia', 'Spain', 'Argentina', 'Puerto Rico',
                 'Papua New Guinea', 'Cuba', 'Jordan', 'St. Vincent and the Grenadines']

    cities = {'Foxborough': 'Boston', 'Commerce City': 'Denver',
              'Frisco': 'Dallas', 'Carson': 'Los Angeles',
              'St.': 'St. Louis', 'Alto': 'Palo Alto',
              'Harrison': 'Newark', 'Sandy': 'Salt Lake City', 'Sandy Utah': 'Salt Lake City',
              'Lakewood Ranch': 'Sarasota', 'Glendale': 'Phoenix',
              'Belo Horizonte': 'Brazil', 'Manaus': 'Brazil'}

    if len(venue) > 4:
        if any(country in venue for country in countries):
            try:
                start = venue.index(',') + 2
            except ValueError:
                start = venue.index(';') + 2
            venue = '@' + venue[start:].strip()
        else:
            try:
                start = venue.index(';') + 1
                try:
                    end = venue.index(',')
                    venue = venue[start:end].strip()
                except ValueError:
                    venue = venue[start + 1:].strip()
            except ValueError:
                pass

    venue = cities[venue] if venue in cities.keys() else venue

    if venue in countries:
        venue = '@' + venue

    return venue


def fix_time(time):
    """
    Change the time format
    :param time: String of time in x:xx PM format
    :return: String of time in x:xxPM ET format
    """
    if 'TBD' not in time:
        inda = time.index("T") + 1
        time = time[:inda]
        time_change = {'ET': 0, 'CT': 1, 'MT': 2, 'PT': 3, 'HT': 5}
        if ':' in time:
            ind = time.index(':')
            local = time[0:ind]
            local = int(local)
            local += time_change[re.compile(r'[A-Z]T').search(time).group()] \
                if re.compile(r'[A-Z]T').search(time).group() in time_change.keys() else local
            if local > 12:
                local -= 12
                if 'PM' in time[ind:].upper() and '12' in time:
                    time = '{}{}'.format(local, time[ind:])
                else:
                    time = '{}{}'.format(local, time[ind:])
            else:
                time = str(local) + time[ind:]
        else:
            ind = time.index(' ')
            local = time[0:ind]
            local = int(local.replace('PM', '').replace('AM', ''))
            local += time_change[re.compile(r'[A-Z]T').search(time).group()] \
                if re.compile(r'[A-Z]T').search(time).group() in time_change.keys() else local
            if local > 12:
                local -= 12
                if 'PM' in time[ind:].upper() and '12' not in time:
                    time = '{}:00 AM'.format(local)
                else:
                    time = '{}:00 PM'.format(local)
            else:
                time = str(local) + ':00' + time[ind:]
    else:
        time = 'TBD '

    time = time.replace(' ET', '').replace(' CT', '').replace(' MT', '')
    time = time.replace('HT', '').replace(' PT', '').replace(' ', '')

    return time


def fix_date(date, now):
    """
    Amend the default date format
    :param date: String of a full date
    :param now: datetime.datetime.now()
    :return: Strings of abbreviated date and current year
    """
    year = date[-4:-1] + date[-1]
    current_year = str(now.year)
    date = date.replace(" " + current_year, '')
    date = date[0:3] + '. ' + date[-3:-1].strip()
    date = date.strip()

    return date, year


def fix_watch(watch):
    """
    Fix the default channel info
    :param watch: String of channel info
    :return: Fixed watch with one channel
    """
    watch = watch.replace('|', '').strip()
    if ',' in watch:
        watch = watch[:watch.index(',')]
    else:
        try:
            watch = watch[:watch.index(' ')]
        except ValueError:
            pass

    watches = {'fox sports 1': 'FS1 ', 'FS1': 'FS1 ', 'fox sports 2': 'FS2 ',
               'FS2': 'FS2 ', 'fox soccer 2': 'FSoc2 ', 'fox soccer plus':
               'FSocP ', 'bein': 'beIN', 'ussoccer.com': 'ussoccer'}

    watch = watches[watch.lower()] if watch.lower() in watches.keys() else watch

    return watch


def fix_matchtype(opponent):
    """
    Determine the match type
    :param opponent: String of team vs opponent
    :return: String of matchtype
    """
    matchtype = 'F'
    countries = ['Mexico', 'Costa Rica', 'Honduras', 'Panama', 'Trinidad']
    if any(country in opponent for country in countries):
        matchtype = 'WCQ'
    return matchtype


def make_schedule(schedule_data, current_year, mnt_times, wnt_times, limit, now):
    """
    Make a string of reddit markup tables that comprise upcoming matches
    :param schedule_data: JSON data of all the upcoming matches
    :param current_year: Current Gregorian year, as a string
    :param mnt_times: How many MNT matches have been done so far
    :param wnt_times: How many WNT matches have been done so far
    :param limit: How many matches per table
    :param now: datetime.datetime.now()
    :return: mnt_table, wnt_table, u23mnt_table, u23wnt_table, u20mnt_table,
            u20wnt_table, mnt_match, wnt_match, mnt_match_today, wnt_match_today
    """
    mnt_table, wnt_table, u23mnt_table, u23wnt_table, u20mnt_table, \
    u20wnt_table = ('', '', '', '', '', '')
    mnt_match, wnt_match = '', ''
    mnt_sendmatch, wnt_sendmatch, mnt_match_today, wnt_match_today = True, True, False, False

    months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
              'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    timelist = [now.month, now.day]

    for match in schedule_data['results']:
        date = match['date']
        try:
            venue = match['venue']
        except KeyError:
            venue = 'TBD'
        try:
            opponent = match['opponent/_text']
            if 'present' in opponent.lower():
                opponent = opponent[:opponent.index('Present')].strip().strip(',').strip('-')
            if 'the ' in opponent:
                opponent = opponent.replace('the ', '')
        except KeyError:
            opponent = 'TBD'
        time = match['time']
        try:
            watch = match['watch'].strip().replace('TICKETS', '')
            watch = re.sub(r'^Ticket Info *', '', watch)
            watch = re.sub(r'^| Buy Tickets *', '', watch)
        except KeyError:
            watch = ' '

        date, year = fix_date(date, now)
        venue = fix_venue(venue)
        watch = fix_watch(watch)
        time = fix_time(time)
        matchtype = fix_matchtype(opponent)

        datelist = [months[date.split('. ')[0]], int(date.split('. ')[1])]

        samemonth = datelist[0] == timelist[0] and datelist[1] >= timelist[1]

        if datelist[0] > timelist[0] or samemonth:
            if 'MNT' in opponent and 'U-' not in opponent and current_year == year and \
                    mnt_times < limit and mnt_sendmatch:
                opponent = re.sub(r'.*MNT vs *', '', opponent)
                mnt_sendmatch = False
                mnt_table = construct_schedule_table('MNT', mnt_table, opponent,
                                                                venue, date, watch, time, matchtype)
                mnt_times += 1
                mnt_match = '{}?{}?{}?{}?{}'.format(opponent, venue, date, watch, time)
                if datelist[0] == timelist[0] and datelist[1] == timelist[1]:
                    mnt_match_today = True

            elif 'MNT' in opponent and 'U-' not in opponent and \
                            current_year == year and mnt_times < limit:
                opponent = re.sub(r'.*MNT vs *', '', opponent)
                mnt_table = construct_schedule_table('MNT', mnt_table, opponent,
                                                     venue, date, watch, time, matchtype)
                mnt_times += 1

            elif 'WNT' in opponent and 'U-' not in opponent and \
                     current_year == year and wnt_times < limit and wnt_sendmatch:
                opponent = re.sub(r'.*WNT vs *', '', opponent)
                wnt_sendmatch = False
                wnt_table = construct_schedule_table('WNT', wnt_table, opponent,
                                                     venue, date, watch, time, matchtype)
                wnt_times += 1
                wnt_match = '{}?{}?{}?{}?{}'.format(opponent, venue, date, watch, time)
                if datelist[0] == timelist[0] and datelist[1] == timelist[1]:
                    wnt_match_today = True

            elif 'WNT' in opponent and 'U-' not in opponent and \
                            current_year == year and wnt_times < limit:
                opponent = re.sub(r'.*WNT vs *', '', opponent)
                wnt_table = construct_schedule_table('WNT', wnt_table, opponent,
                                                     venue, date, watch, time, matchtype)
                wnt_times += 1

            elif 'U-23 MNT' in opponent and current_year == year and u23mnt_table.count('\n') <= limit + 2:
                opponent = re.sub(r'.*U-23 MNT vs *', '', opponent)
                u23mnt_table = construct_schedule_table('U-23 MNT', u23mnt_table, opponent,
                                                        venue, date, watch, time, matchtype)

            elif 'U-23 WNT' in opponent and current_year == year and u23wnt_table.count('\n') <= limit + 2:
                opponent = re.sub(r'.*U-23 WNT vs *', '', opponent)
                u23wnt_table = construct_schedule_table('U-23 WNT', u23wnt_table, opponent,
                                                        venue, date, watch, time, matchtype)

            elif 'U-20 MNT' in opponent and current_year == year and u20mnt_table.count('\n') <= limit + 2:
                opponent = re.sub(r'.*U-20 MNT vs *', '', opponent)
                u20mnt_table = construct_schedule_table('U-20 MNT', u20mnt_table, opponent,
                                                        venue, date, watch, time, matchtype)

            elif 'U-20 WNT' in opponent and current_year == year and u20wnt_table.count('\n') <= limit + 2:
                opponent = re.sub(r'.*U-20 WNT vs *', '', opponent)
                u20wnt_table = construct_schedule_table('U-20 WNT', u20wnt_table, opponent,
                                                        venue, date, watch, time, matchtype)

    return mnt_table, wnt_table, u23mnt_table, u23wnt_table, u20mnt_table, u20wnt_table, mnt_match,\
           wnt_match, mnt_match_today, wnt_match_today


def construct_schedule_table(team, table, opponent, venue, date, watch, time, matchtype):
    """
    Construct a reddit markup table
    :param team: String of team
    :param table: Table
    :param opponent: opponent
    :param venue: Fixed venue
    :param date: Fixed date
    :param watch: Fixed watch
    :param time: Fixed time
    :param matchtype: String of matchtype
    :return: Void, edits table
    """
    if table:
        table += "|[{} ({})](#s)|[{}](#s)|[{} {}](#s)|[{}](#s)|\n".format(opponent, venue,
                                                                          date, watch, time,
                                                                          matchtype)
        return table
    else:
        table = '#{}\n| Team   | Date  | Time (ET)  | ' \
                'Type |\n|:-----------|:------------:|:------------:|----------:|\n'.format(team)
        table += "|[{} ({})](#s)|[{}](#s)|[{} {}](#s)|[{}](#s)|\n".format(opponent, venue,
                                                                          date, watch, time,
                                                                          matchtype)
        return table


def make_results(results_data, mnttimes, wnttimes, limit):
    """
    Construct a reddit markup table of all recent results
    :param results_data: JSON of results data
    :param mnttimes: How many MNT matches have been done so far
    :param wnttimes: How many WNT matches have been done so far
    :param limit: How many matches per table
    :return:
    """
    mnt_results, wnt_results = '', ''
    for match in results_data['results']:
        date = match['date']
        result = match['result']
        opponent = match['opponent/_text']
        if 'present' in opponent.lower():
            opponent = opponent[:opponent.index('Present')].strip().strip(',').strip('-')

        if 'MNT' in opponent and 'U-' not in opponent and mnttimes < limit:
            opponent = re.sub(r'.*MNT vs *', '', opponent)
            mnt_results = construct_results_table('MNT', mnt_results, date, opponent, result)
            mnttimes += 1

        if 'WNT' in opponent and 'U-' not in opponent and wnttimes < limit:
            opponent = re.sub(r'.*WNT vs *', '', opponent)
            wnt_results = construct_results_table('WNT', wnt_results, date, opponent, result)
            wnttimes += 1

        if mnttimes >= limit and wnttimes >= limit:
            break

    return mnt_results, wnt_results


def construct_results_table(team, table, date, opponent, result):
    """
    Construct a reddit markup table
    :param team: US team
    :param table: Table to write/create
    :param date: Date
    :param opponent: Opponent
    :param result: W/D/L
    :return: Edited table
    """
    opponent = opponent.replace('the ', '')
    if 'L' in result:
        result = '[{}](#bar-3-red)'.format(result)
    if 'W' in result:
        result = '[{}](#bar-3-green)'.format(result)
    if 'D' in result:
        result = '[{}](#bar-3-yellow)'.format(result)

    date, __ = fix_date(date, datetime.datetime.now())

    if table:
        table += "|[{}](#s)|[{}](#s)|[{}](#s)|\n".format(opponent, date, result)
        return table
    elif 'MNT' in team:
        table = '\n\n## **RESULTS**\n\n\n#MNT\n| Team   | Date  | Result  |' \
                '\n|:-----------|:------------:|:------------:|\n'
        table += "|[{}](#s)|[{}](#s)|[{}](#s)|\n".format(opponent, date, result)
        return table
    else:
        table = '#WNT\n| Team   | Date  | Result  |' \
                '\n|:-----------|:------------:|:------------:|\n'
        table += "|[{}](#s)|[{}](#s)|[{}](#s)|\n".format(opponent, date, result)
        return table


def create_text(list_tables, now):
    """
    Concatenate all tables together
    :param list_tables: List of tables to be joined
    :param now: datetime.datetime.now()
    :return: String to print to reddit
    """
    line = '\n\n---\n\n'.join(table for table in list_tables if table)
    line += '\n\n[^Last ^updated: ^{0:%m/%d}](#s)\n\n'.format(now)
    return line


def update_sidebar(sub, text, reddit):
    """
    Updates subreddit sidebar
    :param sub: the subreddit to update
    :param text: the text to update the sidebar with
    :param reddit: a PRAW object (note this requires the proper scope to update sidebar settings
    :return: void
    """
    settings = reddit.get_settings(sub)
    sidebar_contents = settings['description']
    text = '[](#start)\n{}'.format(text)
    totalupdate = '{}\n\n{}\n\n{}'.format(sidebar_contents[:sidebar_contents.index('[](#start)')],
                                          text, sidebar_contents[sidebar_contents.index('[](#end)'):])

    reddit.update_settings(reddit.get_subreddit(sub), description=totalupdate)
    results = reddit.get_settings(sub)
    sc = results['description']
    if '{0:%m/%d}'.format(datetime.datetime.now()) in sc:
        return True
    else:
        return False


def new_main(key, refresh_token, access, new_key, new_refresh_token,
             new_access, sendmessage=True, debug=False):
    """
    Runs the program
    :param key: PRAW key
    :param refresh_token: PRAW refresh token
    :param access: PRAW access key
    :param new_key: PRAW key
    :param new_refresh_token: PRAW refresh token
    :param new_access: PRAW access key
    :param sendmessage: Send message T/F
    :param debug: Debug T/F
    :return: Void
    """
    # constants
    mnt_times, wnt_times, mnttimes, wnttimes = 0, 0, 0, 0
    limit = 4
    now = datetime.datetime.now()
    current_year = str(now.year)

    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y',
                        filename='log.log', level=logging.WARNING)
    logging.disable(logging.INFO)

    user_agent = "/r/ussoccer sidebar match updater v2.5 by /u/RedRavens /u/matchThreader"
    redd = praw.Reddit(user_agent, oauth_client_id='3t3dsPvTZPXpQA',
                       oauth_client_secret=key,
                       oauth_redirect_uri='http://127.0.0.1:65010/authorize_callback'
                       )
    redd.config.log_requests = 0
    access_information = {'access_token': access,
                          'refresh_token': refresh_token,
                          'scope': {'account creddits edit flair history '
                                    'identity livemanage modconfig '
                                    'modcontributors modflair modlog modothers '
                                    'modposts modself modwiki '
                                    'mysubreddits privatemessages read '
                                    'report save submit subscribe '
                                    'vote wikiedit wikiread'}
                          }
    access1 = redd.refresh_access_information(access_information['refresh_token'])
    redd.set_access_credentials(**access1)

    importio_link1 = 'https://api.import.io/store/connector/f425f5bf' \
                     '-8b78-45f5-9b6a-4168194e9080/_query?' \
                     'input=webpage/url:http%3A%2F%2F' \
                     'www.ussoccer.com%2Fschedule-tickets&&_apikey=' \
                     '858c84718f394836ae3069d78bd0c657ba94049c' \
                     'e35a11c11f59fda3e8f888bf3583ee138c5546105' \
                     '40819b872d599d449f9d1fe61cf955ef192f88cc228' \
                     'f390eb956dc0e9ed8a8cb528c2c5e33a0a22'

    importio_link2 = 'https://api.import.io/store/connector/30a913e7-d99f' \
                     '-4773-a338-f3b08541ce3d' \
                     '/_query?input=webpage/url:http%3A%2F%2F' \
                     'www.ussoccer.com%2Fresults-statistics&' \
                     '&_apikey=858c84718f394836ae3069d78bd0c657ba94049' \
                     'ce35a11c11f59fda3e8f888bf3583ee138' \
                     'c554610540819b872d599d449f9d1fe61cf955ef192f88cc228f' \
                     '390eb956dc0e9ed8a8cb528c2c5e33a0a22'
    schedule_data = get_importio(importio_link1)
    results_data = get_importio(importio_link2)

    try:
        mnt_table, wnt_table, u23mnt_table, u23wnt_table, u20mnt_table,\
        u20wnt_table, mnt_match, wnt_match, mnt_match_today, wnt_match_today = \
            make_schedule(schedule_data, current_year, mnt_times, wnt_times, limit, now)
        mnt, wnt = make_results(results_data, mnttimes, wnttimes, limit)

        all_tables = [mnt_table, wnt_table, u23mnt_table,
                      u23wnt_table, u20mnt_table, u20wnt_table, mnt, wnt]
        alltext = create_text(all_tables, now)

        updatedsidebar = False
        if not debug:
            updatedsidebar = update_sidebar("ussoccer", alltext, redd)
        else:
            print("{}".format(alltext))

        red = praw.Reddit(user_agent="/u/RedRavens Sending match info V2",
                          oauth_client_id='1bWlWUr4c1UADA',
                          oauth_client_secret=new_key,
                          oauth_redirect_uri='http://127.0.0.1:65010/authorize_callback')
        red.config.log_requests = 0
        access_information = {'access_token': new_access,
                              'refresh_token': new_refresh_token,
                              'scope': {'privatemessages'}
                              }
        access1 = red.refresh_access_information(access_information['refresh_token'])
        red.set_access_credentials(**access1)

        if not mnt_match:
            mnt_match = 'Unable to determine MNT next match'
        if not wnt_match:
            wnt_match = 'Unable to determine WNT next match'

        if sendmessage:
            # TODO: Fix RPI, uncomment these
            red.send_message('ussoccer_bot', 'MNT next match', mnt_match)
            red.send_message('ussoccer_bot', 'WNT next match', wnt_match)
            if mnt_match_today:
                push(mnt_match, 'MNT', redd)
                # red.send_message('ussoccer_bot', "MNT match today", mnt_match)
            if wnt_match_today:
                push(wnt_match, 'WNT', redd)
                # red.send_message('ussoccer_bot', "WNT match today", wnt_match)

        if updatedsidebar and '?' in mnt_match and '?' in wnt_match:
            logging.warning("INFO: Updated sidebar and sent next matches")
        elif not updatedsidebar and not debug:
            logging.error("WARNING: Didn't update sidebar")
        elif 'Unable' in mnt_match:
            logging.error("WARNING: Unable to determine MNT next match")
        elif 'Unable' in wnt_match:
            logging.error("WARNING: Unable to determine WNT next match")

        red.clear_authentication()

    except Exception as excep:
        if not debug:
            redd.send_message('RedRavens', 'Unable to update sidebar',
                              'Unable to update sidebar on {0:%m/%d at %I:%M%p} '
                              'because of {1:}; {2:}'.format(now, excep, traceback.format_exc())
                              )
            logging.exception("ERROR: Couldn't update sidebar because of %s; %s", excep,
                              traceback.format_exc())
        else:
            print("ERROR: Couldn't update sidebar because of {}\n\n{}".format(excep, traceback.format_exc()))

    finally:
        if not debug:
            questions = 0
            for msg in redd.get_unread(unset_has_mail=True, update_user=True, limit=None):
                if 'match thread' in msg.subject.lower() and 'r3d' not in msg.subject.lower():
                    msg.mark_as_read()
                    questions += 1
                    mess = "This bot is for /r/ussoccer only. " \
                           "Please send your request to /u/MatchThreadder (two d's) instead."
                    msg.reply(mess)

            logging.warning('INFO: Wrong bot calls: %i', questions)
        redd.clear_authentication()
        logging.warning("-" * 30)


def startbot():
    if 's/A' in os.getcwd():
        with open('.matchthreader.txt') as filep:
            key_outer, refresh_token_outer, access_outer = filep.read().split('\n')
        with open('.redravens.txt') as filep:
            new_key_outer, new_refresh_token_outer, new_access_outer = filep.read().split('\n')

        new_main(key_outer, refresh_token_outer, access_outer, new_key_outer,
                 new_refresh_token_outer,
                 new_access_outer, sendmessage=False, debug=True)

    else:
        with open('/home/redravens/updater/matchthreader.txt') as filep:
            key_outer, refresh_token_outer, access_outer = filep.read().split('\n')
        with open('/home/redravens/updater/redravens.txt') as filep:
            new_key_outer, new_refresh_token_outer, new_access_outer = filep.read().split('\n')

        new_main(key_outer, refresh_token_outer, access_outer, new_key_outer,
                 new_refresh_token_outer,
                 new_access_outer, sendmessage=True, debug=False)


if __name__ == '__main__':
    try:
        startbot()
    except KeyError:
        print('Encountered KeyError')
        sleep(10)
        try:
            startbot()
        except KeyError:
            print('Encountered KeyError x 2')
            sleep(10)
            try:
                startbot()
            except KeyError:
                print('Encountered KeyError x 3, quitting')
