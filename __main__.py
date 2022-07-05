from webbrowser import get
from dotenv import load_dotenv
from os import getenv
from time import sleep
import requests

load_dotenv()
TOKEN = getenv('DISCOGS_API_TOKEN')
BASE_URL = 'https://api.discogs.com'


def search(**params):
    params = {
        'token': TOKEN,
        'style': 'tech house',
        'country': 'canada',
        'year': '1999',
        'format': 'vinyl'
    }

    url = f'{BASE_URL}/database/search'
    request = requests.get(url, params=params)
    response = request.json()
    return response


def get_full_data(release_id):
    sleep(1)
    url = f'{BASE_URL}/releases/{release_id}?={TOKEN}'
    request = requests.get(url)
    response = request.json()
    return response


def get_rating(release):
    if 'community' in release:
        return release['community']['rating']['average']
    else:
        return None


def rating_above(release, min_rating):
    rating = get_rating(release)
    return rating >= min_rating if rating else False


def main():
    min_rating = 4.0
    search_response = search()
    n_results = search_response['pagination']['items']
    print(f'{n_results} results')

    results = search_response['results']
    release_ids = [r['id'] for r in results]
    releases = [get_full_data(id) for id in release_ids]
    top_rated = [r for r in releases if rating_above(r, min_rating)]
    top_rated = sorted(top_rated, key=get_rating, reverse=True)
    for release in top_rated:
        print(f"{release['artists_sort']} - {release['title']} - {release['year']} - rated {get_rating(release)}")
        print(release['uri'])
        print('\n')


if __name__ == '__main__':
    main()
