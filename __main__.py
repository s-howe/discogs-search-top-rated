from os import getenv
from time import sleep
import argparse
from pathlib import Path

import requests

POSSIBLE_SEARCH_KEYS = [
    "query",
    "type",
    "title",
    "release_title",
    "credit",
    "artist",
    "anv",
    "label",
    "genre",
    "style",
    "country",
    "year",
    "format",
    "catno",
    "barcode",
    "track",
    "submitter",
    "contributor",
]


class DiscogsSearchTopRated:
    def __init__(self) -> None:
        self.validate_env()
        self.base_url = "https://api.discogs.com"
        self.styles_file = Path("./styles.txt")
        self.session = self.setup_session()

    @staticmethod
    def validate_env() -> None:
        if getenv("DISCOGS_API_TOKEN") is None:
            raise EnvironmentError(
                "Please load the DISCOGS_API_TOKEN environment variable. "
                "This can be generated here: https://www.discogs.com/settings/developers"
            )

    @staticmethod
    def setup_session() -> requests.Session:
        """Returns a requests session with the correct headers and params for multiple
        requests to the Discogs API."""
        session = requests.Session()
        session.headers = {"user-agent": "DiscogsSearchTopRated/0.1"}
        session.params = {"token": getenv("DISCOGS_API_TOKEN"), "per_page": 100}
        return session

    def run(
        self, search_params: dict[str, str], min_rating: float, no_videos: bool = False
    ) -> None:
        """Searches for releases matching the given search criteria and outputs the
        results."""
        results = self.search_releases(search_params)

        print(f"{len(results)} results. Finding high rated ones.")

        results = self.filter_results(results, min_rating, no_videos)

        if not len(results):
            print("No search results. Please check your search filters.")

        self.output_results(results)

    def search_releases(self, search_params: dict = None) -> list[dict]:
        """Runs a Discogs search for releases that match the given search params."""
        url = f"{self.base_url}/database/search"
        first_page = self.request(url, params=search_params)
        results = self.paginate(first_page, "results")
        return results

    def filter_results(
        self, results: list[dict], min_rating: float, no_videos: bool = False
    ) -> list[dict]:
        """Filters search results for extra criteria that cannot be included in a
        basic Discogs API search request."""
        # Filter out master releases, these do not have ratings
        results = [r for r in results if r["id"] != r["master_id"]]

        release_ids = [r["id"] for r in results]
        releases = [self.get_full_release(id) for id in release_ids]

        filtered_releases = [r for r in releases if r.rating > min_rating]
        print(f"{len(filtered_releases)} results with high ratings.")

        if no_videos:
            filtered_releases = [r for r in filtered_releases if not r.has_videos]
            print(f"{len(filtered_releases)} results with no videos.")

        return filtered_releases

    def output_results(self, filtered_releases: list[dict]) -> None:
        """Outputs the results to the console."""
        for release in filtered_releases:
            print(f"\n{release}\n{release.data['uri']}")

    def request(
        self, url: str, params: dict[str, str] = None, paginating: bool = False
    ) -> dict:
        """Makes a request to the Discogs API and returns the JSON response.

        Args:
            url: The URL to request.
            params: The params to pass to the request. Defaults to None.
            paginating: Whether this request is part of a pagination
                sequence. Defaults to False.

        Raises:
            ValueError: If the response is not valid JSON.
        """
        # Session-level params are already present in URLs when paginating
        params = {"token": None, "per_page": None} if paginating else params
        response = self.session.get(url, params=params)

        try:
            return response.json()
        except requests.JSONDecodeError:
            raise ValueError(f"{url}\n{response.text}")

    def get_full_release(self, release_id: str) -> "Release":
        """Gets the full release data for a release. This provides more data than is
        given by the basic Discogs API search results e.g. ratings and videos."""
        # Discogs API rate limits at 60 requests per minute.
        sleep(1)
        url = f"{self.base_url}/releases/{release_id}"
        release_data = self.request(url)
        return Release(release_data)

    def update_styles_file(self) -> None:
        """Updates the stored styles file with all the styles from the user's own
        collection."""
        collection = self.get_collection()
        styles = [s.lower() for s in self.get_unique_values(collection, "styles")]
        with self.styles_file.open("w") as fp:
            fp.write("\n".join(styles) + "\n")

    def get_collection(self) -> list[dict]:
        """Returns a list of releases in the user's collection."""
        username = self.get_username()
        url = f"{self.base_url}/users/{username}/collection/folders/0/releases"
        first_page = self.request(url)
        releases = self.paginate(first_page, "releases")
        return releases

    def get_username(self) -> str:
        url = f"{self.base_url}/oauth/identity"
        response = self.request(url)
        return response["username"]

    @staticmethod
    def get_unique_values(releases: list[dict], field_name: str) -> list[str]:
        """Gets unique values for a given release property across a list of releases.
        E.g. to get all the unique styles in a user's collection."""
        all_values = []
        for r in releases:
            for value in r["basic_information"][field_name]:
                all_values.append(value)

        unique_values = list(set(all_values))
        unique_values = sorted(unique_values, key=all_values.count, reverse=True)
        return list(unique_values)

    def paginate(self, first_page: dict, results_key: str) -> list[dict]:
        """Paginates through a multi-page Discogs API response and returns collated
        results."""
        results = first_page[results_key]
        if first_page["pagination"]["pages"] > 1:
            # Discogs API rate limits at 60 requests per minute.
            sleep(1)
            current_page = first_page
            while "next" in current_page["pagination"]["urls"]:
                next_page_url = current_page["pagination"]["urls"]["next"]
                current_page = self.request(next_page_url, paginating=True)
                results += current_page[results_key]
        return results


class Release:
    def __init__(self, data) -> None:
        self.data = data

    def __str__(self) -> str:
        return f"{self.artist} - {self.data['title']} - {self.data['country']} - {self.data['year']} - rated {self.rating}"

    @property
    def artist(self) -> str:
        return self.data["artists"][0]["name"]

    @property
    @property
    def has_videos(self) -> bool:
        return "videos" in self.data and len(self.data["videos"])

    @property
    def rating(self) -> float:
        if "community" in self.data:
            return self.data["community"]["rating"]["average"]
        else:
            # Master releases do not have ratings
            return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-rating",
        type=float,
        default=4.0,
        help="Filters search results for those with ratings above this value.",
    )

    parser.add_argument(
        "--no-videos",
        action="store_true",
        default=False,
        help="Removes releases with videos from results.",
    )

    parser.add_argument(
        "--update-styles",
        action="store_true",
        default=False,
        help="Updates styles.txt with styles from your own collection.",
    )

    for search_field in POSSIBLE_SEARCH_KEYS:
        parser.add_argument(f"--{search_field}", required=False)

    args = parser.parse_args()

    discogs_search_top_rated = DiscogsSearchTopRated()

    if args.update_styles:
        discogs_search_top_rated.update_styles_file()
    else:
        args_dict = vars(args)
        search_params = {
            k: v for k, v in args_dict.items() if k in POSSIBLE_SEARCH_KEYS
        }

        discogs_search_top_rated.run(
            search_params=search_params,
            min_rating=args.min_rating,
            no_videos=args.no_videos,
        )


if __name__ == "__main__":
    main()
