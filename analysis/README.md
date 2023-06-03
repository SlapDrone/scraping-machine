# Analysis

The `analysis` service is a container with a fully-featured python NLP environment intended to process the scraped data.

**I've migrated from using the unofficial ChatGPT API (the only free option available at the time) to the official API and Langchain + LlamaIndex since AAAI 2023**.

It does not depend on any of the other services, although if the `scraper-db` is running it can access it directly on the docker network (see [this notebook](./notebooks/dump_db_to_parquet.ipynb)). I have dumped the database tables to parquet files in the [data](./data/) directory to make performing analysis completely independent for someone cloning the repo.

The container runs a notebook server in the background. It can be accessed by opening the URL displayed when running:

```
docker-compose logs analysis
```

Notebooks are found in the [notebooks directory](./notebooks/).
