import json

from flask import Flask, request, jsonify, Response
import os
import pandas as pd
import google.generativeai as genai
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from scrapy.signalmanager import dispatcher
from scraper.scraper.spiders.AmazonScraping import AmazonSpider
from sentiment_analyzer import analyze_sentiment, get_pros_cons, get_summary
from multiprocessing import Process, Queue as MPQueue

app = Flask(__name__)

def run_spider(urls, results_queue):
    results = []

    def item_scraped(item, response, spider):
        print(f"Item scraped: {item}")
        results.append(item)

    def spider_closed(spider):
        print(f"Spider closed. Total items scraped: {len(results)}")
        df = pd.DataFrame(results)
        if df.empty:
            print("Warning: DataFrame is empty!")
        else:
            print(f"DataFrame info:\n{df.info()}")
        results_queue.put(df)

    process = CrawlerProcess(get_project_settings())
    dispatcher.connect(item_scraped, signal=signals.item_scraped)
    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    try:
        process.crawl(AmazonSpider, start_urls=urls)
        process.start()
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        results_queue.put(pd.DataFrame())

def spider_process(urls, results_queue):
    run_spider(urls, results_queue)

def compose_ad(product_name, summary, pros, cons, product_url):
    genai.configure(api_key=os.environ['GENAI_API_KEY'])

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f'Write a social-media ad for the following product {product_name} \
        Summary: {summary} \
        Pros: {pros} \
        Cons: {cons} \
        Never use markdown styling (no # nor *). \
        Never include internal CSS.\
        The ad should be attractive and inducing, but not misleading. \
        Always encourage customers to purchase. \
        Format the response using html/css only but do not add any format specifiers \
        and do not include the containing <div></div> tags.  \
        Make the ad eye-catching. Use emojis if needed. Do not add images to the ad.\
        Write only the content of the <div> without the <div> tag \
        Add the following product url (in a hyperlink): {product_url} \
        in <a> tag with an attractive label.' \
    )

    return response.text

def process_request(request):
    urls = [request]
    results_queue = MPQueue()

    # Launch a process for web scraping or data extraction
    p = Process(target=spider_process, args=(urls, results_queue))
    p.start()
    data = results_queue.get()
    p.join()

    if data.empty or data['review_body'].isna().all():
        return {
            "product": request,
            "error": "No data was scraped. Please check the URL and try again."
        }

    # Analyze the sentiment and get progress updates
    sentiment_result = None
    for progress_update in analyze_sentiment(data):
        progress_data = json.loads(progress_update)

        if 'result' in progress_data:
            sentiment_result = progress_data['result']
        else:
            yield progress_update  # Yield progress

    genai.configure(api_key=os.environ['GENAI_API_KEY'])

    sentiment_result = json.loads(sentiment_result)
    sentiment_result = pd.DataFrame(sentiment_result)

    pros, cons, summary = get_pros_cons(sentiment_result)
    positive_reviews = sum(sentiment_result['predicted_rating'] == 1)
    negative_reviews = sum(sentiment_result['predicted_rating'] == 0)

    product = data['product'][0]
    price = data['price'][0]
    avg_rating = data['avg_rating'][0]
    image_url = data['image_url'][0]

    # Yield final output as JSON
    yield json.dumps({'insights_result': {
        "product": product,
        "price": price,
        "pros": pros,
        "cons": cons,
        "summary": summary,
        "avg_rating": avg_rating,
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
        "image_url": image_url,
    }})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    def generate():
        for progress_update in process_request(url):
            yield f"{progress_update}\n"  # Stream each progress update back to the client

    # This response will stream progress updates back to the client
    return Response(generate(), mimetype='application/json')

@app.route('/create_ad', methods=['POST'])
def create_ad():
    data = request.json
    product_name = data['product_name']
    summary = data['summary']
    pros = data['pros']
    cons = data['cons']
    product_url = data['product_url']

    ad_text = compose_ad(product_name, summary, pros, cons, product_url)

    print('ad_text: ', ad_text)
    
    return jsonify({'ad_text': ad_text})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)