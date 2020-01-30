#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
usage: get_delay_stat.py $stationid

see https://docs.marudor.de for api-documentation
use https://marudor.de/api/station/v1/searchAll/Berlin for finding your stationid
"""

import sys
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def requests_retry_session(
        retries=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
        session=None,
):
    """Just an auxiliary for requests with retry-option"""
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


STATION = sys.argv[1]

URL_STATION = 'https://marudor.de/api/station/v1/station/' + STATION
DOWNLOAD_STATION = requests_retry_session().get(URL_STATION)
if DOWNLOAD_STATION.status_code != 200:
    print('### HTTP-ERROR ON Station-Info: ' + URL_STATION)
    exit()

DATA_STATION = DOWNLOAD_STATION.content.decode('utf-8')
VALUES_STATION = json.loads(DATA_STATION)
TITLE_STATION = 'Unknown [' + str(STATION) + ']'
if VALUES_STATION['title']:
    TITLE_STATION = '"' + VALUES_STATION['title'] + '" [' + str(STATION) + ']'

URL_DEP = 'https://marudor.de/api/hafas/v1/departureStationBoard?station=' + STATION
DOWNLOAD_DEP = requests_retry_session().get(URL_DEP)

if DOWNLOAD_DEP.status_code != 200:
    print('### HTTP-ERROR ON Departures: ' + URL_DEP)
    exit()

DATA_DEP = DOWNLOAD_DEP.content.decode('utf-8')
VALUES_DEP = json.loads(DATA_DEP)

LATE_SUM = 0
LATE_AMOUNT = 0
EARLY_SUM = 0
EARLY_AMOUNT = 0
CANCELLED = 0

for value in VALUES_DEP:
    if value['departure'] and value['departure']['scheduledTime'] and value['departure']['time']:

        if value['departure']['scheduledTime'] < value['departure']['time']:
            LATE_SUM += value['departure']['time'] - value['departure']['scheduledTime']
            LATE_AMOUNT += 1
        if value['departure']['time'] < value['departure']['scheduledTime']:
            EARLY_SUM += value['departure']['scheduledTime'] - value['departure']['time']
            EARLY_AMOUNT += 1

        try:
            if value['departure']['cancelled']:
                CANCELLED += 1
        except KeyError:
            pass  # -- a not cancelled departure is okay.

# -- print results/statistics
print('Statistics for ' + TITLE_STATION + ': ')
print('------------------------------------------')
print('Amount of Departures: ' + str(len(VALUES_DEP)))
if CANCELLED > 0:
    print('-- Cancelled: ' + str(CANCELLED))
print('-- On Time: ' + str(len(VALUES_DEP) - LATE_AMOUNT - EARLY_AMOUNT))
print('-- early (amount):  ' + str(EARLY_AMOUNT))
print('-- early (minutes): ' + str(EARLY_SUM / 60000))
print('-- late (amount):   ' + str(LATE_AMOUNT))
print('-- late (minutes):  ' + str(LATE_SUM / 60000))
