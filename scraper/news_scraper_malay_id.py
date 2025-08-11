# import libraries
import requests
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import os
import logging
import time
import random
import chardet
from requests.exceptions import RequestException
from lxml import html

# logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./scraper/news_scraper.log'),
        logging.StreamHandler()
    ]
)

# get current date and time 
current_datetime = datetime.datetime.now()
date_str = current_datetime.strftime("%Y-%m-%d")    
time_str = current_datetime.strftime("%H%M")      

# file path config
news_id_folder = './scraper/news_id'
os.makedirs(news_id_folder, exist_ok=True)

# save setup
csv_filename = os.path.join(news_id_folder, f'malay_news_{date_str}_{time_str}.csv')
parquet_filename = os.path.join(news_id_folder, f'malay_news_{date_str}_{time_str}.parquet')

# config
utusan_config = {
    "name": "Utusan Malaysia",
    "base_url": "https://www.utusan.com.my",    
    "id_param": "p",
    "id_range": (100000, 900000),           # for article id
    "num_ids_to_check": 100,                # number of id's to check
    "content_container_xpath": '//*[@id="content"]/div/div/section[3]/div/div/div[1]/div/div/div[5]/div',
    "title_selectors": [
        "h1.jeg_post_title",
        "h1.entry-title",
        "title"
    ],
    "date_selectors": [
        ".jeg_meta_date a", 
        "time.jeg_date",
        "span.jeg_date",
        ".date",
        "time.entry-date",
        "span.posted-on",
        "meta[property='article:published_time']",
        "meta[name='date']"
    ],
    "category_selectors": [
        ".jeg_meta_category a",
        "a.jeg_meta_category",
        ".category",
        "a[rel='category tag']",
        ".post-categories a",
        "span.cat-links a",
        "meta[property='article:section']"
    ]
}

news_items = []
articles_found = 0
articles_excluded = 0

# get random id's
random_ids = random.sample(range(utusan_config['id_range'][0], utusan_config['id_range'][1]), 
                          utusan_config['num_ids_to_check'])

logging.info(f"Checking {utusan_config['num_ids_to_check']} random article IDs from {utusan_config['name']}")

# go through every id generated
for article_id in random_ids:
    try:
        # make a url using the id
        article_url = f"{utusan_config['base_url']}/?{utusan_config['id_param']}={article_id}"
        
        # fetch the article based on made url
        response = requests.get(article_url, timeout=20)
        response.raise_for_status()
        
        # detect encoding if there isn't any
        if response.encoding is None:
            detected_encoding = chardet.detect(response.content)['encoding']
            if detected_encoding:
                response.encoding = detected_encoding
        
        # skip if redirected to homepage
        if response.url == utusan_config['base_url'] + "/" or response.url == utusan_config['base_url']:
            continue
            
        # parse article
        soup = BeautifulSoup(response.text, 'html.parser')
        tree = html.fromstring(response.content)
        
        # extract title
        title = ""
        for selector in utusan_config['title_selectors']:
            try:
                element = soup.select_one(selector)
                if element:
                    title_text = element.get_text().strip()
                    if title_text and title_text != utusan_config['name']:
                        title = title_text
                        break
            except Exception:
                continue
        
        if not title:
            continue
            
        # extract date
        pub_date = ""
        for selector in utusan_config['date_selectors']:
            try:
                # Handle meta tags differently
                if selector.startswith("meta["):
                    element = soup.select_one(selector)
                    if element and element.has_attr('content'):
                        pub_date = element['content'].strip()
                        if pub_date:
                            # Format date from meta tag if needed
                            if "T" in pub_date:
                                pub_date = pub_date.split("T")[0]
                            break
                else:
                    element = soup.select_one(selector)
                    if element:
                        pub_date = element.get_text().strip()
                        if pub_date:
                            break
            except Exception:
                continue
        
        # extract category -- results are empty
        category = ""
        for selector in utusan_config['category_selectors']:
            try:
                # Handle meta tags differently
                if selector.startswith("meta["):
                    element = soup.select_one(selector)
                    if element and element.has_attr('content'):
                        category = element['content'].strip()
                        if category:
                            break
                else:
                    element = soup.select_one(selector)
                    if element:
                        category = element.get_text().strip()
                        if category:
                            break
            except Exception:
                continue
        
        # extract content
        full_content = ""
        try:
            # get XPATH
            container = tree.xpath(utusan_config['content_container_xpath'])

            # get paragraphs
            if container:
                paragraphs = container[0].xpath('.//p')
                
                for p in paragraphs:
                    text_elements = p.xpath('.//text()')
                    paragraph_text = " ".join(text.strip() for text in text_elements if text.strip())
                    
                    # preserve paragraph breaks
                    if paragraph_text:
                        full_content += paragraph_text + "\n\n" 

        except Exception as e:
            logging.warning(f"XPath extraction failed for ID {article_id}: {str(e)}")
        
        # if XPATH failed
        if not full_content.strip():
            try:
                # alternative CSS selectors
                selectors = ['.jeg_post_content', '.entry-content', '.article-content', '.post-content', '.content']
                for selector in selectors:
                    try:
                        content_element = soup.select_one(selector)
                        if content_element:
                            paragraphs = content_element.find_all('p')
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text:
                                    full_content += text + "\n\n"
                            if full_content.strip():
                                break
                    except Exception:
                        continue
            except Exception:
                pass
        
        # strip content extraction
        full_content = full_content.strip()
        
        # skip if content is not found
        if not full_content:
            articles_excluded += 1
            logging.warning(f"Skipping article ID {article_id} - no content found")
            continue
            
        # end on sentence
        last_punct = max(
            full_content.rfind('.'),
            full_content.rfind('!'),
            full_content.rfind('?')
        )
        
        if last_punct != -1:
            summary = full_content[:last_punct + 1]
        else:
            summary = full_content
        
        # add to dataset
        news_items.append({
            "News_Source": utusan_config['name'],
            "Title": title,
            "Source_URL": response.url,
            "Publish_Date": pub_date,
            "Category": category,
            "Summary": summary,
            "Scrape_Date": date_str     # same as in file name
        })
        
        articles_found += 1
        logging.info(f"Found article: ID {article_id} - {title[:50]}...")
        logging.info(f"Date: {pub_date} | Category: {category} | Summary length: {len(summary)} chars")
        time.sleep(random.uniform(1.0, 2.5))    # adjust delay
        
    except RequestException as e:
        logging.warning(f"Request failed for ID {article_id}: {str(e)}")
        time.sleep(3)   
    except Exception as e:
        logging.error(f"Error processing ID {article_id}: {str(e)}")
        time.sleep(1.5)

# create df
if news_items:
    df = pd.DataFrame(news_items)

    # save file
    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        df.to_parquet(parquet_filename, index=False)
        logging.info(f"{articles_found} Utusan articles saved to {csv_filename} and {parquet_filename}")
    except Exception as save_error:
        logging.error(f"Failed to save files: {str(save_error)}")

# log summary
logging.info(f"Scrape completed. IDs checked: {utusan_config['num_ids_to_check']}, "
             f"Articles found: {articles_found}, "
             f"Articles excluded (no content): {articles_excluded}")