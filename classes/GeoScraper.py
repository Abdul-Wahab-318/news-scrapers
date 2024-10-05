import re
import time
import os
import re
import schedule
import requests
from Scraper import Scraper
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
import xml.etree.ElementTree as ET

class GeoScraper(Scraper):

    def __init__(self , rss_url , cache_file_name , source='GEO'):
        self.source = source
        super().__init__( rss_url, cache_file_name)  
        return None

    def preprocess_description(self , description):
        description = description.strip()
        description_cleaned = re.sub(r'&mdash;|<p>|</p>|<p class="">', ' ', description)
        
        return description_cleaned

    def extract_xml(self , root):
    
        news_articles = []
        for item in root[0].iter('item'):
            title = item.find('title').text.strip()
            link = item.find('link').text.strip()
            publish_date = self.preprocess_publish_date(item.find('pubDate').text)

            description_and_image = item.find('description').text.strip().split("\n")
            image_url = self.preprocess_img_url(description_and_image[0])
            
            news_articles.append({
                "title":title , 
                "link" :link , 
                "image_url" : image_url ,
                "publish_date":publish_date ,
                "scraped_date": datetime.now(),
                "source": self.source 
                })
            
        return news_articles

    def extract_content(self , page):
        
        try:
            content_area = page.find('div' , class_="content-area")

            if(not content_area):
                content_area = page.find('div' , class_="long-content")

            content_area_paragraphs = content_area.findAll('p')
            content_area_text = [ paragraph.text for paragraph in content_area_paragraphs]
            content_area_text = " ".join(content_area_text)
            content_area_text = content_area_text.replace('\xa0' , " ")
            
        except Exception as e:
            print("Unknown Error scraping : " , e)
            return None
            
        return content_area_text

    def scrape(self):
        try:
            xml_root = self.get_xml_root(self.rss_url)

            news_articles = self.extract_xml(xml_root)
            latest_news_articles = self.filter_articles(news_articles)
            scraped_news_articles = self.scrape_article_content(latest_news_articles)

            print("prev : " , len(news_articles))
            print("new : " , len(latest_news_articles))
            print('Time : ' , datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
        
            self.save_articles(scraped_news_articles)      
            self.cache_articles(news_articles)
            
        except Exception as e:
            print("Unknown Error : " , e)
            
            
geo_scraper = GeoScraper("https://feeds.feedburner.com/geo/GiKR" , "geo_cache.txt")
geo_scraper.scrape()
