# new_scraper_malay.py (meant to run daily, saving dated csv and parquet files)
# import libraries
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
import datetime
import os
import logging
import time
from requests.exceptions import RequestException

# logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./scraper/news_scraper.log'),
        logging.StreamHandler()
    ]
)

# file path config
today = datetime.datetime.now().strftime("%Y-%m-%d")                        # get today's date

news_feed_folder = './scraper/news_feed'                                                        # setup save folder
os.makedirs(news_feed_folder, exist_ok=True)

csv_filename = os.path.join(news_feed_folder, f'malay_news_{today}.csv')         # setup save pathing
parquet_filename = os.path.join(news_feed_folder, f'malay_news_{today}.parquet')

# source list
news_sources = [
    {"name": "Utusan Malaysia", "url": "https://www.utusan.com.my/feed/"},
    {"name": "Berita Harian", "url": "https://www.bharian.com.my/feed/"},
    {"name": "Harian Metro", "url": "https://www.hmetro.com.my/feed/"},
    {"name": "Kosmo", "url": "https://www.kosmo.com.my/feed/"},
    {"name": "Astro Awani", "url": "https://www.astroawani.com/feeds/posts/default?alt=rss"}
]

news_items = []
failed_sources = []

# go through all sources
for source in news_sources:
    try:
        # fetching
        logging.info(f"Fetching from {source['name']}...")
        response = requests.get(source['url'], timeout=10)
        response.raise_for_status()

        # parsing
        content = response.content
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            for encoding in ['utf-8']:
                try:
                    decoded_content = content.decode(encoding)
                    root = ET.fromstring(decoded_content)
                    break
                except (UnicodeDecodeError, ET.ParseError):
                    continue

        # processing
        for item in root.findall('.//item'):
            try:
                title = item.find('title').text.strip() if item.find('title') is not None else "No Title"
                link = item.find('link').text.strip() if item.find('link') is not None else ""

                # get date
                pub_date = None
                for date_tag in ['pubDate', 'dc:date', 'date']:
                    if item.find(date_tag) is not None:
                        pub_date = item.find(date_tag).text.strip()
                        break

                # get category
                category = None
                for cat_tag in ['category', 'dc:subject']:
                    if item.find(cat_tag) is not None:
                        category = item.find(cat_tag).text.strip()
                        break

                # get summary
                summary = ""
                for desc_tag in ['description', 'content:encoded', 'content']:
                    if item.find(desc_tag) is not None:
                        summary = item.find(desc_tag).text
                        break

                # text cleaning
                if summary:
                    clean_text = re.sub(r'<[^>]+>', '', summary)                                            # HTML tags
                    clean_text = re.sub(r'<!\[CDATA\[|\]\]>', '', clean_text)                               # CDATA
                    clean_text = re.sub(r'\b(img|width|height)="\d+"', '', clean_text)                      # images
                    clean_text = re.sub(r'The post .* appeared first on .*\.', '', clean_text)
                    clean_text = re.sub(r'\.\.\.\s*(Read More).*', '', clean_text, flags=re.IGNORECASE)
                    clean_text = clean_text.strip()

                    # end on sentence
                    last_punct = max(clean_text.rfind('.'),
                                    clean_text.rfind('!'),
                                    clean_text.rfind('?'))
                    if last_punct != -1:
                        clean_text = clean_text[:last_punct + 1]
                else:
                    clean_text = "No summary available"

                # add to dataset
                news_items.append({
                    "News_Source": source['name'],
                    "Title": title,
                    "Source_URL": link,
                    "Publish_Date": pub_date,
                    "Category": category,
                    "Summary": clean_text,
                    "Scrape_Date": today
                })

            except Exception as item_error:
                logging.error(f"Error processing item from {source['name']}: {str(item_error)}")

        logging.info(f"Successfully processed {source['name']}")
        time.sleep(1)

    # error handling
    except RequestException as req_error:
        logging.error(f"Failed to fetch {source['name']}: {str(req_error)}")
        failed_sources.append(source['name'])
    except ET.ParseError as parse_error:
        logging.error(f"Parse error for {source['name']}: {str(parse_error)}")
        failed_sources.append(source['name'])
    except Exception as e:
        logging.error(f"Error with {source['name']}: {str(e)}")
        failed_sources.append(source['name'])

# create df
if news_items:
    df = pd.DataFrame(news_items)

    # save files
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        df.to_parquet(parquet_filename, index=False)
        logging.info(f"{len(df)} news items saved to {csv_filename} and {parquet_filename}")
    except Exception as save_error:
        logging.error(f"Failed to save files: {str(save_error)}")

# failed sources
if failed_sources:
    logging.warning(f"Failed to process {len(failed_sources)} sources: {', '.join(failed_sources)}")

# log summary
logging.info(f"Scrape completed. Total sources: {len(news_sources)}, "
             f"Successful: {len(news_sources) - len(failed_sources)}, "
             f"Failed: {len(failed_sources)}, "
             f"Articles collected: {len(news_items)}")