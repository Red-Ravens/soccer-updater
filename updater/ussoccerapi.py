#!/usr/bin/env python3
#####################################
#    LAST UPDATED     28 MAY 2019   #
#####################################
"""
Scrapes ussoccer.com for Schedule and Results
"""
import requests
import json
import datetime
import pytz
from bs4 import BeautifulSoup


def schedule() -> list:
    """
    Fetch schedule data
    :return: List of matches as tuples
    """
    link = 'http://www.ussoccer.com/schedule-tickets/'
    r = requests.get(link)
    text = r.text
    json_text = text[text.index('id="__JSS_STATE__">'):]
    json_text = json_text.replace('id="__JSS_STATE__">', '')
    json_text = json_text[:json_text.index('</script><script type="application/ld+json">')].strip()
    json_text = json.loads(json_text)
    matches_info = json_text["sitecore"]["route"]["placeholders"]\
        ["jss-main"][0]["placeholders"]["jss-layout-standard-template"][2]["matches"]

    eastern_timezone = pytz.timezone("US/Eastern")

    id_dict = {}

    # get Team ID so that the teams can be filtered later
    for team in json_text["sitecore"]["route"]["placeholders"]\
        ["jss-main"][0]["placeholders"]["jss-layout-standard-template"][2]["teams"]:
        name = str(team["name"]).replace('\xa0', ' ')
        opta_id = team["optaId"]
        id_dict[opta_id] = name


    matches = []  # (date, time, opponent, venue, watch)

    for match in matches_info:
        date_time = match["dateTime"]
        date_time = datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%SZ')
        est_time = eastern_timezone.fromutc(date_time)
        # date = '{0:%b %d}'.format(est_time)
        time = '{0:%I:%M%p}'.format(est_time)
        venue = match["venue"]["country"]
        if match["contestants"][0]["code"] == 'USA':
            team_name = id_dict[match["contestants"][0]["id"]].replace("Men's National Team", "MNT")
            team_name = team_name.replace("Women's National Team", "WNT").replace('U.S. ', '')
            opponent = match["contestants"][1]["name"]
        else:
            team_name = id_dict[match["contestants"][1]["id"]].replace("Men's National Team", "MNT")
            team_name = team_name.replace("Women's National Team", "WNT").replace('U.S. ', '')
            opponent = match["contestants"][0]["name"]

        opponent = '{} vs {}'.format(team_name, opponent).replace("U20", '').replace("U23", '').replace("U17", '').strip()
        comp = match["competition"]["name"]
        comp_code = match["competition"]["code"]
        try:
            watch = match["sitecoreData"]["link1"]["value"]["text"]
        except KeyError:
            watch = 'TBD'


        matches.append([est_time, time, opponent, venue, watch, comp, comp_code])


    return matches


def results() -> list:
    """
    Fetches results data from the link
    :return: List of match results as a tuple
    """
    link = 'http://www.ussoccer.com/schedule-tickets/'
    r = requests.get(link)
    text = r.text
    json_text = text[text.index('id="__JSS_STATE__">'):]
    json_text = json_text.replace('id="__JSS_STATE__">', '')
    json_text = json_text[:json_text.index('</script><script type="application/ld+json">')].strip()
    json_text = json.loads(json_text)
    matches_info = json_text["sitecore"]["route"]["placeholders"] # \
      #  ["jss-main"][0]["placeholders"]["jss-layout-standard-template"][2]["matches"]

    with open('/Users/Alex/Desktop/output.json', 'w') as files:
        json.dump(matches_info, files)

    text = requests.get(link).text
    soup = BeautifulSoup(text, "html.parser")
    matches = []  # (date, opponent, result)

    for num, tr in enumerate(soup.find('table', class_='card-table match-results match-table').find_all('tr')):
        if num != 0:
            for _ in tr:
                date, opponent, result, __, __, __ = [td.get_text(' ', strip=True) for td in tr('td')]
                if len(matches) > 0:
                    if matches[-1][1] != opponent:  # matches[-1][0] != date and
                        matches.append((date, opponent, result))
                    else:
                        pass
                else:
                    matches.append((date, opponent, result))
    return matches


if __name__ == '__main__':
    # results()
    exe = schedule()
    for line in exe:
        print(line)
