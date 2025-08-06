# new_scraper_malay.py
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspaces/ner_news_malay/scraper/news_scraper.log'),
        logging.StreamHandler()
    ]
)

# File path configuration
today = datetime.datetime.now().strftime("%Y-%m-%d")
news_id_folder = '/workspaces/ner_news_malay/scraper/news_id'
os.makedirs(news_id_folder, exist_ok=True)

csv_filename = os.path.join(news_id_folder, f'malay_news{today}.csv')
parquet_filename = os.path.join(news_id_folder, f'malay_news{today}.parquet')

# Website configuration
SOURCE_NAME = "Utusan Malaysia"
BASE_URL = "https://www.utusan.com.my"
ID_RANGE = (100000, 900000)  # Estimated ID range
NUM_IDS_TO_CHECK = 100  # Number of random IDs to check per run

news_items = []
valid_ids_found = 0

# Generate random IDs to check
random_ids = random.sample(range(ID_RANGE[0], ID_RANGE[1]), NUM_IDS_TO_CHECK)

logging.info(f"Checking {NUM_IDS_TO_CHECK} random article IDs from {SOURCE_NAME}")

for article_id in random_ids:
    try:
        # Construct the URL
        article_url = f"{BASE_URL}/?p={article_id}"
        
        # Fetch the article page
        response = requests.get(article_url, timeout=15)
        response.raise_for_status()
        
        # Skip if redirected to homepage
        if response.url == BASE_URL + "/" or response.url == BASE_URL:
            logging.info(f"ID {article_id} redirected to homepage - skipping")
            time.sleep(0.5)
            continue
            
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if it's a valid article page
        title_tag = soup.find('title')
        if not title_tag or title_tag.text.strip() == "Utusan Malaysia":
            logging.info(f"ID {article_id} not a valid article page - skipping")
            time.sleep(0.5)
            continue
            
        # Extract title
        title = title_tag.text.strip()
        
        # Extract date
        pub_date = ""
        date_element = soup.select_one(".jeg_meta_date a")
        if not date_element:
            date_element = soup.select_one(".date")
        if date_element:
            pub_date = date_element.text.strip()
        
        # Extract category
        category = ""
        category_element = soup.select_one(".jeg_meta_category a")
        if not category_element:
            category_element = soup.select_one(".category a")
        if category_element:
            category = category_element.text.strip()
        
        # Extract content - more robust approach
        content = ""
        content_element = None
        
        # Try multiple selectors
        selectors = [
            ".content-inner .jeg_post_content",
            ".entry-content",
            ".article-content",
            ".post-content",
            ".jeg_post_content",
            ".content"
        ]
        
        for selector in selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if content_element:
            # Remove unwanted elements but keep paragraph tags
            for element in content_element.select('script, style, iframe, .ad-container, .jeg_share_button, .related-posts, .comments, .social-share'):
                element.decompose()
                
            # Get text content while preserving paragraph structure
            paragraphs = content_element.find_all(['p', 'div'])
            content = " ".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            content = re.sub(r'\s+', ' ', content).strip()
        
        # Create summary - fallback to title if no content
        if content:
            # Try to get first 2 paragraphs as summary
            summary = " ".join(content.split()[:200])
            last_punct = max(summary.rfind('.'), summary.rfind('!'), summary.rfind('?'))
            if last_punct > 0:
                summary = summary[:last_punct + 1]
            else:
                # If no punctuation, just take first 200 words
                summary = " ".join(content.split()[:200])
        else:
            # Fallback to title if no content found
            summary = title
        
        # Add to results
        news_items.append({
            "News_Source": SOURCE_NAME,
            "Unique_ID": article_id,
            "Title": title,
            "Source_URL": response.url,
            "Publish_Date": pub_date,
            "Category": category,
            "Summary": summary,
            "Scrape_Date": today
        })
        
        valid_ids_found += 1
        logging.info(f"Found valid article: ID {article_id} - {title}")
        logging.info(f"Summary length: {len(summary)} characters")
        time.sleep(1)
        
    except RequestException as req_error:
        logging.error(f"Request failed for ID {article_id}: {str(req_error)}")
        time.sleep(2)
    except Exception as e:
        logging.error(f"Error processing ID {article_id}: {str(e)}")
        time.sleep(1)

# Create DataFrame
if news_items:
    df = pd.DataFrame(news_items)
    
    # Save files
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        df.to_parquet(parquet_filename, index=False)
        logging.info(f"{len(df)} articles saved to {csv_filename} and {parquet_filename}")
    except Exception as save_error:
        logging.error(f"Failed to save files: {str(save_error)}")

# Final log
logging.info(f"Scrape completed. IDs checked: {NUM_IDS_TO_CHECK}, "
             f"Valid articles found: {valid_ids_found}")