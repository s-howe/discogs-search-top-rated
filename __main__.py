from os import getenv
from time import sleep
import argparse
from pathlib import Path

import requests

POSSIBLE_SEARCH_KEYS = [
    'query',
    'type',
    'title',
    'release_title',
    'credit',
    'artist',
    'anv',
    'label',
    'genre',
    'style',
    'country',
    'year',
    'format',
    'catno',
    'barcode',
    'track',
    'submitter',
    'contributor'
]


class DiscogsSearchTopRated(object):
    def __init__(self):
        self.validate_env()
        self.base_url = 'https://api.discogs.com'

        self.styles_file = Path('./styles.txt')

        self.session = requests.Session()
        self.session.headers = {'user-agent': 'DiscogsSearchTopRated/0.1'}
        self.session.params = {'token': getenv('DISCOGS_API_TOKEN')}

        self.args = self.parse_args()
        if self.args.update_styles:
            self.update_styles_file()

    @staticmethod
    def validate_env():
        if getenv('DISCOGS_API_TOKEN') is None:
            raise EnvironmentError('Please load the DISCOGS_API_TOKEN environment variable. '
                                   'This can be generated here: https://www.discogs.com/settings/developers')

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--min-rating', type=float, default=4.0,
                            help='Filters search results for those with ratings above this value.')

        parser.add_argument('--update-styles', action='store_true', default=False,
                            help='Updates styles.txt with styles from your own collection.')

        for search_field in POSSIBLE_SEARCH_KEYS:
            parser.add_argument(f'--{search_field}', required=False)

        args = parser.parse_args()
        return args

    def request(self, url, params=None):
        if params:
            response = self.session.get(url, params=params)
        else:
            response = self.session.get(url)
        try:
            return response.json()
        except requests.JSONDecodeError:
            raise ValueError(f'{url}\n{response.text}')

    def run(self):
        results = self.search()
        # Filter out master releases, these do not have ratings
        results = [r for r in results if r['id'] != r['master_id']]

        if not len(results):
            print('No search results. Please check your search filters.')
            return

        print(f'{len(results)} results. Finding high rated ones.')

        release_ids = [r['id'] for r in results]
        releases = [self.get_full_release_data(id) for id in release_ids]

        top_rated = [r for r in releases if r is not None and self.rating_above(r, self.args.min_rating)]

        top_rated = sorted(top_rated, key=self.get_rating, reverse=True)

        print(f'{len(top_rated)} results with high ratings:')

        for release in top_rated:
            print(f"\n{release['artists_sort']} - {release['title']} - {release['country']} - "
                  f"{release['year']} - rated {self.get_rating(release)}")
            print(release['uri'])

    def search(self):
        search_fields = self.get_search_fields()

        url = f'{self.base_url}/database/search'

        first_page = self.request(url, params=search_fields)
        results = self.paginate(first_page, 'results')
        return results

    def get_search_fields(self):
        all_args = vars(self.args)
        search_fields = {k: v for k, v in all_args.items()
                         if k in POSSIBLE_SEARCH_KEYS and v is not None}
        return search_fields

    def get_full_release_data(self, release_id):
        # Discogs API rate limits at 60 requests per minute.
        sleep(1)
        url = f'{self.base_url}/releases/{release_id}'
        release = self.request(url)
        return release

    def rating_above(self, release, min_rating):
        rating = self.get_rating(release)
        return rating >= min_rating if rating else False

    @staticmethod
    def get_rating(release):
        if 'community' in release:
            return release['community']['rating']['average']
        else:
            return None

    def update_styles_file(self):
        collection = self.get_collection()
        styles = [s.lower() for s in self.get_unique_values(collection, 'styles')]
        with self.styles_file.open('w') as fp:
            fp.write('\n'.join(styles) + '\n')

    def get_collection(self):
        username = self.get_username()

        url = f'{self.base_url}/users/{username}/collection/folders/0/releases'
        first_page = self.request(url)
        releases = self.paginate(first_page, 'releases')
        return releases

    def get_username(self):
        url = f'{self.base_url}/oauth/identity'
        response = self.request(url)
        return response['username']

    @staticmethod
    def get_unique_values(releases, field_name):
        all_values = []
        for r in releases:
            for value in r['basic_information'][field_name]:
                all_values.append(value)

        unique_values = list(set(all_values))
        unique_values = sorted(unique_values, key=all_values.count, reverse=True)
        return list(unique_values)

    def paginate(self, first_page, results_key):
        results = first_page[results_key]
        if first_page['pagination']['pages'] > 1:
            # Discogs API rate limits at 60 requests per minute.
            sleep(1)
            current_page = first_page
            while 'next' in current_page['pagination']['urls']:
                next_page_url = current_page['pagination']['urls']['next']
                current_page = self.request(next_page_url)
                results += current_page[results_key]
        return results


if __name__ == '__main__':
    discogs_search_top_rated = DiscogsSearchTopRated()
    discogs_search_top_rated.run()
