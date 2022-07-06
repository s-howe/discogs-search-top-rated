from dotenv import load_dotenv
from os import getenv
from time import sleep
from pprint import pprint
import argparse
import requests
from pathlib import Path
import json

load_dotenv()


class DiscogsSearchTopRated(object):
    def __init__(self):
        self.base_url = 'https://api.discogs.com'

        self.styles_file = Path('./styles.txt')

        self.session = requests.Session()
        self.session.headers = {'user-agent': 'DiscogsSearchTopRated/0.1'}
        self.session.params = {'token': getenv('DISCOGS_API_TOKEN')}

        self.args = self.parse_args()
        if self.args.update_styles:
            self.update_styles_file()
        elif any(x is None for x in [self.args.style, self.args.country, self.args.year]):
            raise ValueError('Please provide a value for all of --style, --country, --year.')

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--style', choices=self.get_styles(), action='store', type=str)
        parser.add_argument('--country', type=str)
        parser.add_argument('--year', type=str)
        parser.add_argument('--min-rating', type=float, default=4.0)
        parser.add_argument('--update-styles', type=bool, default=False)
        args = parser.parse_args()
        return args

    def get_username(self):
        url = f'{self.self.base_url}/oauth/identity'
        response = self.session.get(url).json()
        return response['username']

    def get_collection(self):
        username = self.get_username()

        url = f'{self.base_url}/users/{username}/collection/folders/0/releases'
        first_page = self.session.get(url).json()
        releases = first_page['releases']

        if first_page['pagination']['pages'] > 1:
            current_page = first_page
            while 'next' in current_page['pagination']['urls']:
                sleep(1)
                next_page_url = current_page['pagination']['urls']['next']
                current_page = self.session.get(next_page_url).json()
                releases += current_page['releases']

        return releases

    def search(self):
        params = {
            'style': self.args.style,
            'country': self.args.country,
            'year': self.args.year,
            'format': 'vinyl'
        }

        url = f'{self.base_url}/database/search'

        first_page = self.session.get(url, params=params).json()
        results = first_page['results']
        if first_page['pagination']['pages'] > 1:
            sleep(1)
            current_page = first_page
            while 'next' in current_page['pagination']['urls']:
                next_page_url = current_page['pagination']['urls']['next']
                current_page = self.session.get(next_page_url).json()
                results += current_page['results']

        return results

    @staticmethod
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

    def get_full_data(self, release_id):
        sleep(1.5)
        url = f'{self.base_url}/releases/{release_id}'
        request = self.session.get(url)
        response = request.json()

        # Verify response
        if 'message' in response:
            print(response['message'])
        else:
            release = self.get_required_information(response)
            del response
            return release

    @staticmethod
    def get_rating(release):
        if 'community' in release:
            return release['community']['rating']['average']
        else:
            return None

    def rating_above(self, release, min_rating):
        rating = self.get_rating(release)
        return rating >= min_rating if rating else False

    @staticmethod
    def get_unique_values(releases, field_name):
        all_values = []
        for r in releases:
            for value in r['basic_information'][field_name]:
                all_values.append(value)

        unique_values = list(set(all_values))
        unique_values = sorted(unique_values, key=all_values.count, reverse=True)
        return list(unique_values)

    def update_styles_file(self):
        collection = self.get_collection()
        styles = [s.lower() for s in self.get_unique_values(collection, 'styles')]
        with self.styles_file.open('w') as fp:
            fp.write('\n'.join(styles) + '\n')

    def get_styles(self):
        with self.styles_file.open('r') as fp:
            return [l.strip() for l in fp.readlines()]

    def run(self):
        results = self.search()
        # Filter out master releases, these do not have ratings
        results = [r for r in results if r['id'] != r['master_id']]

        print(f'{len(results)} results. Finding high rated ones.')

        release_ids = [r['id'] for r in results]
        releases = [self.get_full_data(id) for id in release_ids]

        top_rated = [r for r in releases if r is not None and self.rating_above(r, self.args.min_rating)]

        top_rated = sorted(top_rated, key=self.get_rating, reverse=True)
        print(f'{len(top_rated)} results with high ratings:')
        for release in top_rated:
            print(f"{release['artists_sort']} - {release['title']} - {release['year']} - rated {self.get_rating(release)}")
            print(release['uri'])
            print('\n')


if __name__ == '__main__':
    discogs_search_top_rated = DiscogsSearchTopRated()
    discogs_search_top_rated.run()
