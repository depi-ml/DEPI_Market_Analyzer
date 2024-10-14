import json
import re
import scrapy
from scrapy.http import Request
from scraper.scraper.items import AmazonscrapItem

class AmazonSpider(scrapy.Spider):
    name = 'amazon'

    def __init__(self, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', [])
        if not self.start_urls:
            self.logger.error("No start URLs provided. Please provide at least one URL to scrape.")

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse, errback=self.errback_httpbin)

    def errback_httpbin(self, failure):
        self.logger.error(f"Error on {failure.request.url}: {str(failure.value)}")

    def parse(self, response):
        if "captcha" in response.url or "ap/signin" in response.url:
            self.logger.error(f"Blocked or redirected to login. URL: {response.url}")
            return

        product = response.css('#productTitle::text').get()
        avg_rating = response.css('span#acrPopover span.a-size-base.a-color-base::text').get().strip()

        image_url = response.css('img.a-dynamic-image::attr(src)').get()

        price_parts = response.css(
            'span[aria-hidden="true"] > span.a-price-symbol::text, span[aria-hidden="true"] > span.a-price-whole::text'
        ).getall()[:2]
        fraction = response.css('span[aria-hidden="true"] > span.a-price-fraction::text').get()
        if fraction:
            price_parts.append(f".{fraction}")
        price = ''.join(price_parts).strip()

        review_blocks = response.css('.review')

        if not review_blocks:
            self.logger.warning(f"No reviews found on page: {response.url}")

        for review in review_blocks:
            items = AmazonscrapItem()

            review_body = review.css('.review-text-content span::text').get()
            review_rating = review.css('.review-rating span::text').get()

            helpful_text = review.css('.cr-vote-text::text').get()
            helpful_votes = '0'
            if helpful_text:
                helpful_votes = helpful_text.strip().split()[0]
                if helpful_votes.lower() == 'one':
                    helpful_votes = '1'

            items['product'] = product.strip() if product else None
            items['avg_rating'] = avg_rating if avg_rating else None
            items['price'] = price.strip() if price else None
            items['review_body'] = review_body.strip() if review_body else None
            items['image_url'] = image_url.strip() if price else None

            if review_rating:
                rating_number = self.extract_rating_number(review_rating)
                items['ratings'] = float(rating_number) if rating_number else None
            else:
                items['ratings'] = None

            items['avg_rating'] = float(avg_rating) if avg_rating else None

            items['helpful_votes'] = helpful_votes

            yield items

        next_page = response.css('li.a-last a::attr(href)').get()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                # cookies=self.cookies,
                errback=self.errback_httpbin
            )

    def extract_rating_number(self, rating_string: str) -> str:
        match = re.search(r'(\d+(\.\d+)?)', rating_string)
        return match.group(1) if match else None
