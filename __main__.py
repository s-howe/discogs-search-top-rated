from dotenv import load_dotenv
from os import getenv
from time import sleep
from pprint import pprint
import argparse
import requests
from pathlib import Path
import json

load_dotenv()
TOKEN = getenv('DISCOGS_API_TOKEN')
BASE_URL = 'https://api.discogs.com'
HEADERS = {'user-agent': 'DiscogsSearchTopRated/0.1'}


def get_username():
    params = {
        'token': TOKEN
    }

    url = f'{BASE_URL}/oauth/identity'
    response = requests.get(url, params=params).json()
    return response['username']


def get_collection():
    params = {
        'token': TOKEN
    }

    username = get_username()

    url = f'{BASE_URL}/users/{username}/collection/folders/0/releases'

    session = requests.Session()
    first_page = session.get(url, params=params, headers=HEADERS).json()
    releases = first_page['releases']

    if first_page['pagination']['pages'] > 1:
        current_page = first_page
        while 'next' in current_page['pagination']['urls']:
            sleep(1)
            next_page_url = current_page['pagination']['urls']['next']
            current_page = session.get(next_page_url).json()
            releases += current_page['releases']

    return releases


def search(style, country, year):
    params = {
        'token': TOKEN,
        'style': style,
        'country': country,
        'year': year,
        'format': 'vinyl'
    }

    url = f'{BASE_URL}/database/search'

    session = requests.Session()
    first_page = session.get(url, params=params, headers=HEADERS).json()
    results = first_page['results']
    if first_page['pagination']['pages'] > 1:
        sleep(1)
        current_page = first_page
        while 'next' in current_page['pagination']['urls']:
            next_page_url = current_page['pagination']['urls']['next']
            current_page = session.get(next_page_url).json()
            results += current_page['results']

    return results


def get_required_information(release):
    required_information = {}
    required_information['id'] = release['id']
    required_information['community'] = release['community']
    required_information['uri'] = release['uri']
    required_information['artists_sort'] = release['artists_sort']
    required_information['year'] = release['year']
    required_information['title'] = release['title']
    del release
    return required_information


def get_full_data(release_id):
    sleep(1.5)
    params = {
        'token': TOKEN
    }
    url = f'{BASE_URL}/releases/{release_id}'
    request = requests.get(url, params=params, headers=HEADERS)
    response = request.json()

    # Verify response
    if 'message' in response:
        print(response['message'])
    else:
        release = get_required_information(response)
        del response
        return release


def get_rating(release):
    if 'community' in release:
        return release['community']['rating']['average']
    else:
        return None


def rating_above(release, min_rating):
    rating = get_rating(release)
    return rating >= min_rating if rating else False


def get_unique_values(releases, field_name):
    all_values = []
    for r in releases:
        for value in r['basic_information'][field_name]:
            all_values.append(value)

    unique_values = list(set(all_values))
    unique_values = sorted(unique_values, key=all_values.count, reverse=True)
    return list(unique_values)


def update_styles_file():
    collection = get_collection()
    styles = [s.lower() for s in get_unique_values(collection, 'styles')]
    with Path('./styles.txt').open('w') as fp:
        fp.write('\n'.join(styles) + '\n')


def get_styles():
    with Path('./styles.txt').open('r') as fp:
        return [l.strip() for l in fp.readlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--style', choices=get_styles(), action='store', type=str)
    parser.add_argument('--country', type=str)
    parser.add_argument('--year', type=str)
    parser.add_argument('--min-rating', type=float, default=4.0)
    args = parser.parse_args()

    results = search(args.style, args.country, args.year)
    # Filter out master releases, these do not have ratings
    results = [r for r in results if r['id'] != r['master_id']]

    # results = results[:150]

    with Path('./current_run_search_results.json').open('w') as fp:
        json.dump(results, fp, indent=4)

    print(f'{len(results)} results')

    release_ids = [r['id'] for r in results]
    releases = [get_full_data(id) for id in release_ids]

    with Path('./current_run_releases.json').open('w') as fp:
        json.dump(releases, fp, indent=4)

    top_rated = [r for r in releases if r is not None and rating_above(r, args.min_rating)]

    with Path('./current_run_top_rated.json').open('w') as fp:
        json.dump(top_rated, fp, indent=4)

    top_rated = sorted(top_rated, key=get_rating, reverse=True)
    print(f'{len(top_rated)} results with high ratings:')
    for release in top_rated:
        print(f"{release['artists_sort']} - {release['title']} - {release['year']} - rated {get_rating(release)}")
        print(release['uri'])
        print('\n')


if __name__ == '__main__':
    main()
