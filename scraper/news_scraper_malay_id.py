# new_scraper_utusan.py
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import datetime
import os
import logging
import time
import random
from requests.exceptions import RequestException

# logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspaces/ner_news_malay/scraper/news_scraper.log'),
        logging.StreamHandler()
    ]
)

# file path config
today = datetime.datetime.now().strftime("%Y-%m-%d")
news_id_folder = '/workspaces/ner_news_malay/scraper/news_id'
os.makedirs(news_id_folder, exist_ok=True)

csv_filename = os.path.join(news_id_folder, f'utusan_news_{today}.csv')
parquet_filename = os.path.join(news_id_folder, f'utusan_news_{today}.parquet')

# Utusan Malaysia configuration
utusan_config = {
    "name": "Utusan Malaysia",
    "base_url": "https://www.utusan.com.my",
    "id_param": "p",
    "id_range": (100000, 900000),
    "num_ids_to_check": 100,
    "title_selector": "title",
    "date_selector": ".jeg_meta_date a",
    "category_selector": ".jeg_meta_category a",
    # Updated to get all paragraphs in the content container
    "content_container": "/html/body/div[6]/div/div/div/section[3]/div/div/div[1]/div/div/div[5]/div"
}

news_items = []
articles_found = 0

# Generate random IDs to check
random_ids = random.sample(range(utusan_config['id_range'][0], utusan_config['id_range'][1]), 
                          utusan_config['num_ids_to_check'])

logging.info(f"Checking {utusan_config['num_ids_to_check']} random article IDs from {utusan_config['name']}")

for article_id in random_ids:
    try:
        # Construct the URL
        article_url = f"{utusan_config['base_url']}/?{utusan_config['id_param']}={article_id}"
        
        # Fetch the article page
        response = requests.get(article_url, timeout=15)
        response.raise_for_status()
        
        # Skip if redirected to homepage
        if response.url == utusan_config['base_url'] + "/" or response.url == utusan_config['base_url']:
            continue
            
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if it's a valid article page
        title_tag = soup.find(utusan_config['title_selector'])
        if not title_tag or title_tag.text.strip() == utusan_config['name']:
            continue
            
        # Extract title
        title = title_tag.text.strip()
        
        # Extract date
        pub_date = ""
        date_element = soup.select_one(utusan_config['date_selector'])
        if date_element:
            pub_date = date_element.text.strip()
        
        # Extract category
        category = ""
        category_element = soup.select_one(utusan_config['category_selector'])
        if category_element:
            category = category_element.text.strip()
        
        # Extract all paragraphs from content container
        content_paragraphs = []
        try:
            # Find the content container using XPath-like structure
            container = soup.select_one('body > div:nth-child(6) > div > div > div > section:nth-child(3) > div > div > div:nth-child(1) > div > div > div:nth-child(5) > div')
            
            if container:
                # Extract all paragraph elements
                paragraphs = container.find_all('p')
                
                # Collect text from each paragraph
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text:  # Skip empty paragraphs
                        content_paragraphs.append(text)
        except Exception as e:
            logging.warning(f"Couldn't extract content for ID {article_id}: {str(e)}")
        
        # Combine paragraphs into full content
        full_content = " ".join(content_paragraphs)
        
        # Create summary ending on a sentence
        summary = full_content
        if full_content:
            # Find the last sentence-ending punctuation in the entire content
            last_punct = max(
                full_content.rfind('.'),
                full_content.rfind('!'),
                full_content.rfind('?')
            )
            
            if last_punct != -1:
                summary = full_content[:last_punct + 1]
            else:
                # If no punctuation found, use the entire content
                summary = full_content
        else:
            summary = "No content available"
        
        # Add to dataset
        news_items.append({
            "News_Source": utusan_config['name'],
            "Title": title,
            "Source_URL": response.url,
            "Publish_Date": pub_date,
            "Category": category,
            "Summary": summary,
            "Scrape_Date": today
        })
        
        articles_found += 1
        logging.info(f"Found article: ID {article_id} - {title[:50]}...")
        logging.info(f"Summary length: {len(summary)} characters")
        time.sleep(random.uniform(0.5, 1.5))  # Random delay between requests
        
    except RequestException:
        time.sleep(2)  # Longer delay on request failure
    except Exception as e:
        logging.error(f"Error processing ID {article_id}: {str(e)}")
        time.sleep(1)

# create df
if news_items:
    df = pd.DataFrame(news_items)

    # save files
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        df.to_parquet(parquet_filename, index=False)
        logging.info(f"{articles_found} Utusan articles saved to {csv_filename} and {parquet_filename}")
    except Exception as save_error:
        logging.error(f"Failed to save files: {str(save_error)}")

# log summary
logging.info(f"Scrape completed. IDs checked: {utusan_config['num_ids_to_check']}, "
             f"Articles found: {articles_found}")