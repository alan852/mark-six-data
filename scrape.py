import calendar
from datetime import datetime
import json
import os
from pathlib import Path
import shutil

import requests


baseurl = 'https://bet2.hkjc.com/marksix/getJSON.aspx/?sd={year}{month:02}{first_day:02}&ed={year}{month:02}{last_day:02}&sb=0'
results_dir = './data/results'
history_results_dir = os.path.join(results_dir, 'history')
latest_filename = os.path.join(results_dir, 'latest.json')
draws_filename = os.path.join(results_dir, 'draws.json')


def months(start_year, start_month):
    today = datetime.today()
    if start_year == today.year and start_month == today.month:
        yield start_year, start_month, today.day
        return
    _, last_day = calendar.monthrange(start_year, start_month)
    yield start_year, start_month, last_day
    yield from months(start_year = start_year + start_month // 12, start_month = start_month % 12 + 1)


def beautify_results(results):
    results['date'] = datetime.strptime(results['date'], '%d/%m/%Y').strftime('%Y-%m-%d')
    results['no'] = [int(_) for _ in results['no'].split('+')]
    results['sno'] = int(results['sno'])
    return results


def get_results(url):
    r = requests.get(url)
    r.raise_for_status()
    try:
        for results in r.json():
            yield beautify_results(results)
    except:
        pass


def save_results(results):
    dir = os.path.join(history_results_dir, results['date'][:4])
    if not os.path.exists(dir):
        os.makedirs(dir)
    filename = os.path.join(dir, f'{results['id'].replace('/', '_')}.json')
    if not os.path.isfile(filename):
        with open(filename, 'w') as f:
            json.dump(results , f)


def get_latest_results_date(default_year = 1993, default_month = 1):
    if not os.path.isfile(latest_filename):
        return default_year, default_month, 1
    with open(latest_filename) as f:
        results = json.load(f)
        date = datetime.strptime(results['date'], '%Y-%m-%d')
        return date.year, date.month, date.day


def save_latest_results():
    year_dir = sorted(os.listdir(history_results_dir), reverse = True)[0]
    last_results_file = sorted(os.listdir(os.path.join(history_results_dir, year_dir)), reverse = True)[0]
    shutil.copyfile(os.path.join(history_results_dir, year_dir, last_results_file), latest_filename)


def save_draws():
    draws = {}
    for year in sorted(os.listdir(history_results_dir)):
        year_draws = [_.replace('_', '/').split('.')[0] for _ in sorted(os.listdir(os.path.join(history_results_dir, year)))]
        draws[year] = {'first': year_draws[0], 'last': year_draws[-1]}
    with open(draws_filename, 'w') as f:
        json.dump(draws , f)


if __name__ == '__main__':
    start_year, start_month, _ = get_latest_results_date()
    for year, month, last_day in months(start_year = start_year, start_month = start_month):
        print(f'Getting results between {year}-{month}-1 and {year}-{month}-{last_day}')
        for results in get_results(baseurl.format(year = year, month = month, first_day = 1, last_day = last_day)):
            save_results(results)
    save_latest_results()
    save_draws()
