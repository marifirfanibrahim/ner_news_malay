NER

This repository includes:
1. scraper: to scrape Malaysian news online
2. Gliner NER model (in progress): predicting labels on scraped news
3. tokenizer (for studying): to tokenize scraped news
4. transformer (for studying): for the NER model

A. Data Collection
News article are collected by using the scraper. There are two scrapers used - each using a slightly different approach.

One is parsing the articles directly from the news feed. Following this approach, while providing a quicker runtime and more articles per run, each of these articles can only provide the summary of the article, or even shorter. Since the articles are found on the feed page, there tends to be a "Read more..." at the end of the short summary, oftenly without finishing the last sentence. Another issue is that the articles that appear on the feed page updates ever so often. Meaning that this approach only works on the most recent of news, casting older ones out into the archive.

Another one is using random id's to find articles to parse. This approach constructs a url using randomeized id's. Then it parses any articles that exists from that id. While this method gives a more dynamic reach of articles, going through randomized id's prolongs the runtime. Picture 100 scanned id's but only found 25 to be viable. However, the best part of this approach is that more text can be provided from each article. And, since the id's are random, it is safe to say that every article found for every run would be different. So, more article, more text! Given time can be spared.

Even so, to have more data overall, it would be better to use both approaches. One to provide more rows of data of different contexts, and the other for deeper insight on individual contexts. Best of both worlds!

