#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./run_crawler.sh <crawler_name>"
  exit 1
fi

# Define the command to run the crawler
crawler_name=$1
command="docker compose exec scraper poetry run scrapy crawl $crawler_name"

# Function to handle the keyboard interrupt
trap_interrupt() {
  echo -e "\nKeyboard interrupt detected. Stopping the script."
  exit 0
}

# Set up the trap to catch keyboard interrupt signal
trap trap_interrupt INT

# Run the command in an infinite loop
while true; do
  echo "Running the $crawler_name crawler..."
  $command
  status=$?
  if [ $status -ne 0 ]; then
    echo "Crawler failed with exit status $status. Restarting..."
  else
    echo "Crawler finished successfully. Restarting..."
  fi
  sleep 1
done
