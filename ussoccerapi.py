#!/usr/bin/env python3.5
#####################################
#    LAST UPDATED     26 FEB 2017   #
#####################################
"""
Scrapes ussoccer.com for Schedule and Results
"""
import requests
from bs4 import BeautifulSoup


def schedule() -> list:
    """
    Fetch schedule data
    :return: List of matches as tuples
    """
    link = 'http://www.ussoccer.com/schedule-tickets/'
    text = requests.get(link).text
    soup = BeautifulSoup(text, "html.parser")
    matches = []  # (date, time, opponent, venue, watch)

    for num, tr in enumerate(soup.find('table', class_='card-table upcoming-matches match-table').find_all('tr')):
        if num != 0:
            for _ in tr:
                date, time, opponent, venue, watch = [td.get_text(' ', strip=True) for td in tr('td')]
                if watch == '  ' or not watch:
                    watch = '?'
                watch = watch.replace('Ticket Info | Buy Tickets ', '')
                if len(matches) > 0:
                    if matches[-1][0] != date and matches[-1][1] != time:
                        matches.append((date, time, opponent, venue, watch))
                    elif matches[-1][1] != time:
                        # Potential duplicate? Can't really remember why this if statement is necessary
                        matches.append((date, time, opponent, venue, watch))
                    else:
                        pass
                else:
                    matches.append((date, time, opponent, venue, watch))
    return matches


def results() -> list:
    """
    Fetches results data from the link
    :return: List of match results as a tuple
    """
    link = 'http://www.ussoccer.com/results-statistics/'
    text = requests.get(link).text
    soup = BeautifulSoup(text, "html.parser")
    matches = []  # (date, opponent, result)

    for num, tr in enumerate(soup.find('table', class_='card-table match-results match-table').find_all('tr')):
        if num != 0:
            for _ in tr:
                date, opponent, result, __, __, __ = [td.get_text(' ', strip=True) for td in tr('td')]
                if len(matches) > 0:
                    if matches[-1][0] != date and matches[-1][1] != opponent:
                        matches.append((date, opponent, result))
                    else:
                        pass
                else:
                    matches.append((date, opponent, result))
    return matches
