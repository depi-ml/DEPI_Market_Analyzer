import pandas as pd

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher
from scrapy import signals

from scraper.scraper.spiders.AmazonScraping import AmazonSpider


def run_spider_get_dataframe(urls):
    results = []

    def item_scraped(item, response, spider):
        results.append(item)

    def spider_closed(spider):
        print(f"Spider closed: {spider.name}")

    # Create a CrawlerProcess with project settings
    process = CrawlerProcess(get_project_settings())

    # Connect the item_scraped signal
    dispatcher.connect(item_scraped, signal=signals.item_scraped)
    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    # Start the crawling process
    process.crawl(AmazonSpider, start_urls=urls)
    process.start()  # This will block until the crawling is finished

    # Convert the results to a DataFrame
    df = pd.DataFrame(results)

    print(df.info())

    return df