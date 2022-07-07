# Discogs Search Top Rated

This Python project runs a search on the Discogs API and then filters the search results for those with ratings above 
the specified minimum rating.

## Installation

Install Python and [Poetry](https://python-poetry.org/). 

Run `poetry install` to install the necessary dependencies and `poetry shell` to enter
the virtual environment.

## Requirements

Running the code requires a Discogs API token. This should be set as the `DISCOGS_API_TOKEN` environment variable.

This token can be generated [here](https://www.discogs.com/settings/developers).

## Usage

Example:

``` bash
python . --style "deep house" --country germany --year 1997 --format vinyl --min-rating 4.5

119 results. Finding high rated ones.
28 results with high ratings:

Vargas Girl - Vargas Girl EP - Germany - 1997 - rated 5.0
https://www.discogs.com/release/3049134-Vargas-Girl-Vargas-Girl-EP

Boo Williams - Technical E.P. - Germany - 1997 - rated 5.0
https://www.discogs.com/release/13031948-Boo-Williams-Technical-EP

Various - 4 Seasons EP Vol. 2 - Germany - 1997 - rated 5.0
https://www.discogs.com/release/1172186-Various-4-Seasons-EP-Vol-2
...
```

All available countries are listed in the `countries.txt` file. Available styles are listed in the `styles.txt` file. These are generated from the author's collection. To generate a list of styles from your own collection, run

``` bash
python . --update-styles
```

The `--min-rating` argument has a default value of 4.0.

All available search arguments:
* --query
* --type
* --title
* --release_title
* --credit
* --artist
* --anv
* --label
* --genre
* --style
* --country
* --year
* --format
* --catno
* --barcode
* --track
* --submitter
* --contributor
