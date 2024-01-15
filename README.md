# Discogs Search Top Rated

This Python project runs a search on the Discogs API and then filters the search results for those with ratings above 
the specified minimum rating.

## Motivation

Discogs currently offers a fairly good search implementation in their web GUI. However, a user cannot filter by the 
community rating of a release. Community ratings tend to be correlated with the quality of a release, so this project 
adds a minimum rating filter to search results, narrowing them down to higher quality releases.

## Installation

### Prerequisites

**Python**: This project requires Python 3.6 or higher.
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Steps

1. Clone the repository
``` bash
git clone https://github.com/s-howe/discogs-search-top-rated
cd discogs-search-top-rated
```

2. (Optional) Set up a virtual environment
``` bash
python -m venv venv
source venv/bin/activate
```

3. Install the required packages
``` bash
pip install -r requirements.txt
```

## Setting environment variables

Running the code requires a Discogs API token. This should be set as the `DISCOGS_API_TOKEN` environment variable.

This token can be generated [here](https://www.discogs.com/settings/developers).

Set the environment variable in your shell before running the code:
``` bash
export DISCOGS_API_TOKEN=your_token_here
```

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

All available countries are listed in the `countries.txt` file. Available styles are listed in the `styles.txt` file. 
These are generated from the author's collection. To generate a list of styles from your own collection, run

``` bash
python . --update-styles
```

The `--min-rating` argument has a default value of 4.0.

To limit the highly-rated results to those without videos, pass the `--no-videos` argument.

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

Search tips:
* The `--year` argument can take ranges e.g. `--year "1994-1999"`
* The `--style` argument appears to search for styles containing any of the words in the given string e.g. `--style "deep tech house"` will return results with both 'deep house' and 'tech house' styles

## Ideas for further development

Contributions are very welcome. Current ideas:
* --output option
    * html - output/open a HTML file which lists the results, complete with images and release info
    * txt - output to a text file instead of stdout
* Convert to a proper CLI rather than `python . ...`
