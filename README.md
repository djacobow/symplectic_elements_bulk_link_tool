# Overview

This repo contains some wrapper code for using the Symplectic Elements API,
as well as a few programs that use that code to do things.

## `link_maker.py`

`link_maker.py` is a command line tool to allow the creation of links
in Elements between publications and users (claiming) or between publications
and grants (funding linking), working in bulk from a .csv or .tsv file.

### Basic Usage

The tool is quite simple. It expects, at a minimum, two files. One contains
credentials for Elements in JSON format. An example is provided. The second
can be a comma- or tab-separated file that contains three columns: doi,
user, and grant. For each row in that file, you must provide a DOI and 
either a user, a grant name, or both, for the tool to link tool.

For example, this file would be a valid input:
```csv
doi,user,grant
"10.1016/j.copbio.2017.03.014","jdkeasling@lbl.gov","High Energy Physics"
"10.1016/j.biortech.2017.05.001","jdkeasling@lbl.gov","Federal Bureau of Investigation"
```

As would this one:

```csv
doi,user,grant
"10.1016/j.biortech.2017.05.001","jdkeasling@lbl.gov",
"10.1016/j.copbio.2017.03.014",,"High Energy Physics"
```

### Command-line options

required:

    `-infile <csv_file_to_act_on>`
    `-pw     <credentials_file.json>`

optional:

    `-jr <json result file to write>`
    `-cr <csv result file to write>`

    (if you leave these out, you will get default "results.json" and "results.csv")

    `-tab` if using tsv rather than csv)

    `-fake` 
    look up each pub, user, and grant, and check to see if linking is
    possible, but do not actually create any links

    `-debug`
    print out extra debug info while running

### `fetch_cache.json`

Using the Symplectic API can be very slow. As a result, it's convenient
to cache things. Since often you will be re-running this tool after running
in -fake mode, it is nice to cache what you can.

`link_maker.py` will therefore right everything it "GETs" from Symplectic
into a a huge json file, which it will then read again when you run the 
tool second time. This greatly speeds up re-runs when you make a small
change or whatever.

Of course, pubs and users have changed, this file can get stale. And it 
also can get huge. You can delete it at any time if you want to get the 
latest info from the real Symplectic database.

## `bulk_rejector.py` and `reject_from_csv.py`

Sometimes it's convenient to be able to programmatically reject (disclaim)
pubs in bulk.

These tools work using the same API wrappers as `link_maker.py` and
use similar command-line arguments. `bulk_rejector.py` takes a list of 
email address on the command line and rejects all their unclaimed pubs.

`reject_from_csv.py` works more like `link_maker.py`, taking a csv 
spreadsheet of DOIs and usernames, and rejects the publications listed.

#### Author

dgj@lbl.gov

#### Version & History

0.01 -- very preliminary 
