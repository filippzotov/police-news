# Police News Aggregator

This project contains a script that runs every 24 hours to gather news about police shootings from various news APIs. The collected news articles are then processed and filtered using ChatGPT. The filtered news is stored in a Google Sheets document and an email summary is sent out.

## Features

- Fetches news articles from multiple news APIs.
- Filters and processes news articles using ChatGPT.
- Stores filtered news articles in a Google Sheets document.
- Sends an email summary of the filtered news.

## Requirements

- Python 3.x
- Google Sheets API credentials
- Email service credentials
- News API keys
- OpenAI API key for ChatGPT

## Running with Docker Compose

To run the Police News Aggregator using Docker Compose, follow these steps:

1. Ensure you have Docker and Docker Compose installed on your machine.
2. Create a `.env` file in the project root directory and add the necessary environment variables (API keys, credentials, etc.).
3. Build and start the containers using Docker Compose:

   ```sh
   docker-compose up --build
   ```

4. The script will now run every 24 hours as scheduled.

To stop the containers, use:

```sh
docker-compose down
```
