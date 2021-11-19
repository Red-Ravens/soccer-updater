#!/usr/bin/env python3
#####################################
#    LAST UPDATED     19 NOV 2021   #
#####################################
"""
Scrapes ussoccer.com for Schedule and Results
"""
import re
import requests
import datetime
from bs4 import BeautifulSoup


def schedule() -> list:
    """
    Fetch schedule data
    :return: List of matches as tuples
    """
    def fetch(url: str, team: str) -> list:
        """

        :return: list of date, time, opponent, '', tv, '', competition]
        """
        toreturn = []

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)             '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95'}
        text = requests.get(url, headers=headers).text
        soup = BeautifulSoup(text, features="html.parser")

        table = soup.find('table', class_='Table')

        try:
            for i, tr in enumerate(table):
                if i == 2:
                    for td in tr:
                        date = ''
                        time = ''
                        opponent = ''
                        tv = ''
                        competition = ''
                        us_first = False
                        for ind, tr2 in enumerate(td):
                            if ind == 0:
                                date = datetime.datetime.strptime(tr2.text, '%a, %b %d').replace(
                                    year=datetime.datetime.now().year)
                            if ind == 1:
                                if tr2.text.upper().strip() == 'UNITED STATES':
                                    us_first = True
                                else:
                                    opponent = '{} vs {}'.format(team, tr2.text)
                            if ind == 3:
                                if us_first:
                                    opponent = '{} vs {}'.format(team, tr2.text)
                                else:
                                    continue
                            if ind == 4:
                                time = tr2.text
                            if ind == 5:
                                competition = tr2.text
                            if ind == 6:
                                tv = tr2.text
                        toreturn.append((date, time, opponent, '', tv, '', competition))
        except TypeError:
            return []

        return toreturn

    matches = []

    url1 = 'https://www.espn.com/soccer/team/fixtures/_/id/660/united-states'
    url2 = 'https://www.espn.com/soccer/team/fixtures/_/id/2765/united-states'
    url3 = 'https://www.espn.com/soccer/team/fixtures/_/id/2829/united-states-u23'
    url4 = 'https://www.espn.com/soccer/team/fixtures/_/id/2833/united-states-u20'

    mnt = fetch(url1, 'MNT')
    wnt = fetch(url2, 'WNT')
    u23mnt = fetch(url3, 'U-23 MNT')
    u20mnt = fetch(url4, 'U-20 MNT')

    if mnt:
        for line in mnt:
            matches.append(line)

    if wnt:
        for line in wnt:
            matches.append(line)

    if u23mnt:
        for line in u23mnt:
            matches.append(line)

    if u20mnt:
        for line in u20mnt:
            matches.append(line)

    # [date, time, opponent, venue, TV, competition, competition code]
    return matches
    

def results() -> list:
    """
    Fetches results data from the link
    :return: List of match results as a tuple
    """
    def fetch(url: str, team: str) -> list:
        """

        :return: list of date, time, opponent, '', tv, '', competition]
        """
        toreturn = []

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)             '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95'}
        text = requests.get(url, headers=headers).text
        soup = BeautifulSoup(text, features="html.parser")

        table = soup.find('table', class_='Table')

        try:
            for i, tr in enumerate(table):
                if i == 2:
                    for td in tr:
                        date = ''
                        time = ''
                        opponent = ''
                        tv = ''
                        competition = ''
                        us_first = False
                        for ind, tr2 in enumerate(td):
                            if ind == 0:
                                date = datetime.datetime.strptime(tr2.text, '%a, %b %d').replace(
                                    year=datetime.datetime.now().year)
                            if ind == 1:
                                if tr2.text.upper().strip() == 'UNITED STATES':
                                    us_first = True
                                else:
                                    opponent = '{} vs {}'.format(team, tr2.text)
                            if ind == 3:
                                if us_first:
                                    opponent = '{} vs {}'.format(team, tr2.text)
                                else:
                                    continue
                            if ind == 4:
                                time = tr2.text
                            if ind == 5:
                                competition = tr2.text
                            if ind == 6:
                                tv = tr2.text
                        toreturn.append((date, time, opponent, '', tv, '', competition))
        except TypeError:
            return []

        return toreturn

    matches = []

    url1 = 'https://www.espn.com/soccer/team/results/_/id/660/united-states'
    url2 = 'https://www.espn.com/soccer/team/results/_/id/2765/united-states'
    url3 = 'https://www.espn.com/soccer/team/results/_/id/2829/united-states-u23'
    url4 = 'https://www.espn.com/soccer/team/results/_/id/2833/united-states-u20'

    mnt = fetch(url1, 'MNT')
    wnt = fetch(url2, 'WNT')
    u23mnt = fetch(url3, 'U-23 MNT')
    u20mnt = fetch(url4, 'U-20 MNT')

    if mnt:
        for line in mnt:
            matches.append(line)

    if wnt:
        for line in wnt:
            matches.append(line)

    if u23mnt:
        for line in u23mnt:
            matches.append(line)

    if u20mnt:
        for line in u20mnt:
            matches.append(line)

    return matches


def schedule2() -> list:
    """
    Construct a schedule via FotMob links. Not currently used.
    :return: list of tuples with (date, kickoff time, team vs opponent, blank, tv, blank, type)
    """
    def fetch(url: str, team: str) -> list:
        holding_list = []
        toreturn = []

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)             '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95'}
        text = requests.get(url, headers=headers).text
        soup = BeautifulSoup(text, features="html.parser")

        table = soup.find('div', class_="css-177ackh-FixturesCardCSS e13iyrxf0")
        for index, thing in enumerate(table):
            if index >= 2:
                temp_list = []
                for ind, a in enumerate(thing):
                    if ind == 0:
                        if a.text:
                            temp_list.append(a.text)

                    else:
                        temp_list.append(a.text)

                if len(temp_list) == 2:
                    # length = 3 is a result, not an upcoming game
                    holding_list.append(temp_list)

        for match in holding_list:
            time = match[0]
            everything_else = match[1]

            # fix date first
            try:
                time_dtime = datetime.datetime.strptime(time[0:11], '%a, %d %b').date()
            except ValueError:
                try:
                    time_dtime = datetime.datetime.strptime(time, '%d %B %Y').date()
                except ValueError:
                    time_dtime = None

            # get time of match
            time = re.compile(r'(\d)+:(\d)+').search(everything_else).group()
            hour = int(time.split(':')[0])
            if hour > 12:
                hour -= 12
                flag = 'PM'
            else:
                flag = 'AM'
            fixed_time = '{}:{} {}'.format(hour, time.split(':')[1], flag)

            # get team and opponent
            splitter = '/-|'
            everything_else = everything_else.replace(time, splitter)
            team, opponent = everything_else.split(splitter)
            toreturn.append([time_dtime, fixed_time, team, opponent])

        return toreturn

    return fetch('https://www.fotmob.com/teams/6713/overview/usa', 'MNT')


if __name__ == '__main__':
    """
    #exe = results()
    """
    exe = schedule()
    for line_ in exe:
        print(line_)

    # schedule2()
