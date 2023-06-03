# ML conference scraper and analysis

Web scrapers for Machine Learning conference pages. Intended to aid performing quantitative statistical analysis on the natural language content of the research presented.

## Overview

The codebase comprises a set of services managed by Docker. These are:

- A [scrapy](https://scrapy.org/) project containing the scraping code and associated execution environment 
- A [scrapy-splash](https://github.com/scrapy-plugins/scrapy-splash) server for scraping Javascript which runs in the background (usually required on modern conference websites). **I have migrated SPA scraping to [Scrapy-Playwright](https://github.com/scrapy-plugins/scrapy-playwright) which uses [Playwright](https://playwright.dev/python/) since AAAI2023**.
- A [postgreSQL](https://www.postgresql.org/) database for storing the scraped conference data which runs in the background
- A [pgAdmin](https://www.pgadmin.org/) server for querying and interacting with the above database from your web browser which runs in the background (optional)
- An analysis environment for interacting with the database in python (via e.g. jupyter notebooks) and doing some NLP/stats on its content

Each entry has a corresponding container in the [top level compose file](../docker-compose.yml) which also defines some environment variables, database credentials etc. This provides
a complete environment for running locally. In principle components also can be spun up and used independently if you know what you're doing of course.

## Quick start

To get started locally (assuming you have Docker and docker-compose installed):

### If you want to do analysis of conference data

Bring up the analysis environment by running:

```
docker-compose up analysis -d
```

This will open a notebook server that you can access by obtaining the URL from:

```
docker-compose logs analysis
```

### If you want to do everything (Scraper, database server, analysis environment)

Bring up the complete environment *(this is heavier on your computer)* by running:

```
docker-compose up -d
```

from the root of the repo (e.g. here).

## Further info

Once the environment is built and running, if you would like to:

- Run an existing scraper (and populate the database), implement a new scraper, or test/interactively scrape a conference website, refer to the [scraper readme](./scraper/README.md)
- Perform analysis in python, refer to the [analysis readme](./analysis/README.md)
- Interact independently with/change something about the database, refer to the [database readme](./db/README.md)