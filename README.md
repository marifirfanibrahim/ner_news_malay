# NER for Malaysian news in Malay language

This repository includes:
1. scraper: to scrape Malaysian news online
2. model_gliner (in progress): using the gliner model to predict labels on scraped news
3. tokenizer (for studying): to tokenize scraped news
4. transformer (for studying): for the NER model

## A. Data Collection
News article are collected by using the scraper. There are two scrapers used - each using a slightly different approach. One is parsing the articles directly from the news feed [link](#feed-approach). Another one is using random id's to find articles to parse [link](#id-approach). 

Generally, to have more data overall, it would be better to use both approaches. One to provide more rows of data of different contexts, and the other for deeper insight on individual contexts. Best of both worlds!

### Feed-approach
The `scraper/news_scraper_malay_feed.py` file excecutes the scraping multiple news websites feed pages. These are:
- https://www.utusan.com.my/feed
- https://www.bharian.com.my/feed/
- https://www.hmetro.com.my/feed/
- https://www.kosmo.com.my/feed/ 
- https://www.astroawani.com/feeds/posts/default?alt=rss

Following this approach, while providing a quicker runtime and more articles per run, each of these articles can only provide the summary of the article, or even shorter. Since the articles are found on the feed page, there tends to be a "Read more..." at the end of the short summary, oftenly without finishing the last sentence. Another issue is that the articles that appear on the feed page updates ever so often. Meaning that this approach only works on the most recent of news, casting older ones out into the archive.

### ID-approach
This approach uses the `scraper/news_scraper_malay_id.py` file. It scrapes news articles based on randomized id's. In this code, it gets the data from the https://www.utusan.com.my. This approach constructs a url using randomeized id's. Then it parses any articles that exists from that id. While this method gives a more dynamic reach of articles, going through randomized id's prolongs the runtime. Picture 100 scanned id's but only found 25 to be viable. However, the best part of this approach is that more text can be provided from each article. And, since the id's are random, it is safe to say that every article found for every run would be different. So, more article, more text! Given time can be spared.

### Handling Mutiple Files of Data
The `scraper/join_csv.py` was made to join all the csv and parquet files into one file respectively. This is easen the data cleaning and preparation for the NER model. The merged file will be saved at `model_gliner/malay_news.csv` and `model_gliner/malay_news.parquet` resepectively.

## B. Data Labeling
The labels that will be used for this model is as follows:

|  Label  |  Entity  |
|  ---    |  ---     |
|GPE|Geopolitical| 
|PERSON|People
|ORG|Organization
|FAC|Facility
|MONEY|Monetary
|NORP|Nationalities/ Religious/ Political Groups 
|LOC|Location
|PRODUCT|Products
|EVENT|Events
|PERCENT|Percentage
|WORK_OF_ART|Titles of Creative Works
|TIME|Time
|ORDINAL|Ordinal Numbers
|CARDINAL|Cardinal Numbers
|QUANTITY|Measurements
|LAW|Named Documents Made Into Laws|

### Labelling Prediction
The `model_gliner/prediction_main.ipynb` file will be used to predict the labels on the text data gathered from the news scraping in Part A. Here, The `model_gliner/malay_news.parquet` file is extracted of its title and summary column entries. These extractions are put in seperate sentences into a txt file. The txt file, `model_gliner/malay_news_corpus.txt`, is then used with the gliner model for the prediction. The specific gliner used for this is the `urchade/gliner_multi`, which supports the Malay language.
