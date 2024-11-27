import feedparser
from fuzzywuzzy import fuzz
import csv
import os
import schedule
import time

# List of RSS feed URLs
rss_feeds = [
    "https://www.sbsun.com/feed/",
    "https://www.westsidestorynewspaper.com/feed/",
    "https://www.nbclosangeles.com/tag/san-bernardino/feed/",
    "https://sanbernardinonewsdaily.com/feed/",
    "https://sb-american.com/feed/",
    "https://www.latimes.com/local/rss2.0.xml",
    "https://www.dailynews.com/feed/",
    "https://www.nbclosangeles.com/?rss=y",
    "https://www.ocregister.com/feed/",
    "https://abc7.com/tag/orange-county/feed/",
    "https://www.pe.com/feed/",
    "https://abc7.com/tag/riverside/feed/",
    "https://www.sbsun.com/feed/",
    "https://www.nbclosangeles.com/tag/san-bernardino/feed/",
]

# Keywords to search for in articles
keywords = [
    "officer involved shooting",
    "unarmed person shot by the police",
    "police shooting",
    "deputy shooting",
    "officer involved shooting",
    "deputy involved shooting",
    "shots fired by police",
    "police killing",
    "suspect shot at",
    "man killed by police",
    "woman killed by police",
    "CHP shooting",
    "park ranger shooting",
    "law enforcement shooting",
    "police use of deadly force",
    "person died in custody",
    "death in custody of police",
]

# Set a threshold for fuzzy matching (e.g., 70%)
threshold = 70
csv_file = "news_results.csv"


# Check if the article already exists in CSV
def article_exists(title):
    if not os.path.exists(csv_file):
        return False

    with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if title == row[0]:  # Title is in the first column
                return True
    return False


# Function to append a new article to CSV
def append_to_csv(title, link, date, description):
    with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([title, link, date, description])


# Function to parse and filter RSS feeds based on fuzzy matching with keywords
def parse_rss_feeds(feed_urls, keywords, threshold):
    for url in feed_urls:
        print(f"\nParsing feed: {url}")
        feed = feedparser.parse(url)
        if not feed.entries:
            print("No entries found in this feed.")
        for entry in feed.entries:
            entry_title = entry.get("title", "")
            entry_description = entry.get("description", "")
            entry_text = entry_title + " " + entry_description

            # Check for fuzzy matches with each keyword
            for keyword in keywords:
                match_ratio = fuzz.partial_ratio(keyword.lower(), entry_text.lower())
                print(
                    f"Checking entry '{entry_title}': Match ratio with '{keyword}' = {match_ratio}"
                )

                if match_ratio >= threshold:
                    if not article_exists(entry_title):
                        entry_link = entry.get("link", "No link available")
                        entry_date = entry.get("published", "No date available")

                        print(f"\nAdding Article: {entry_title}")
                        print(f"Link: {entry_link}")
                        print(f"Published date: {entry_date}")
                        print(f"Description: {entry_description}")
                        print("-----")

                        # Append the new article to CSV
                        append_to_csv(
                            entry_title, entry_link, entry_date, entry_description
                        )
                    else:
                        print(f"Duplicate found: '{entry_title}' already in CSV.")
                    break


# Schedule the function to run every 20 minutes
def job():
    print("Checking RSS feeds for new articles...")
    parse_rss_feeds(rss_feeds, keywords, threshold)
    print("Check complete.")


# Initialize CSV with headers if file does not exist
if not os.path.exists(csv_file):
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Link", "Published Date", "Description"])

# Run once initially to populate the file if there are matches
job()

# Run the job every 20 minutes
schedule.every(20).minutes.do(job)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)
