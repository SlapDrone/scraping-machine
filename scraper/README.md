# Scrapers

This is a containerised scrapy environment to scrape conference proceedings (articles, talks, workshops...) and dump them in a postgres database.

Currently implemented conferences and their associated implemented spiders are:

- [ICML 2022](https://icml.cc/virtual/2022/index.html) ("icml_2022_crawler")
- [NeurIPS 2022](https://neurips.cc/Conferences/2022) ("neurips_2022_crawler")
- [AAAI 2023 (*WIP*)](https://underline.io/events/380/reception) ("aaai_2023_crawler")

## Instructions

Each conference is scraped by running a scrapy spider. Each spider proceeds through all the links in the conference site and extracts items one by one to a postgres database. This takes time and CPU resources, as multiple pages are scraped simultaneously (how many is configurable in [settings](./settings.py), default is four) and most require interacting with dynamic content via javascript. Once the spider has finished running, the scrapy process will exit. Running the spider is simple:

### Bring up the container
A given scraper is run from the docker environment, so first bring up a container.

The recommended way to do this locally is to bring up the complete environment (including the database, splash server and other necessary components) from the [top level compose file](../docker-compose.yml) by running:

```
docker-compose up -d
```

from the root of the repo.

### Launch a spider

#### In the background

A crawler can be launched as a background process in its container. After bringing up the environment, do:

```
docker-compose exec scraper poetry run scrapy crawl <spider_name>
```

If using the compose file, you can follow its logs by running:

```
docker-compose logs scraper
```

Alternatively, just query the database tables as they are populated in real time via pgAdmin on the browser at [port 8080](localhost:8080).

#### From an interactive shell

A crawler can be initiated within an interactive shell in the container. After bringing up the environment, do:

```
docker-compose exec scraper /bin/bash
```

and then:

```
poetry run scrapy crawl <spider_name>
```


