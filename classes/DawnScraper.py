import re
from classes.Scraper import Scraper
from datetime import datetime
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

class DawnScraper(Scraper):

    def __init__(self , rss_url = "https://www.dawn.com/feeds/home" , source='Dawn'):
        super().__init__( rss_url, source)  
        return None

    def preprocess_description(self , description):
        html = BeautifulSoup(description , 'lxml')
        description = html.get_text().strip().replace('\n' ,' ')
        description = self.clean_text(description)
        return description

    def extract_articles_from_xml(self , root):
    
        news_articles = []
        namespaces = {'media': 'http://search.yahoo.com/mrss/'}
            
        for item in root.findall('.//item'):
            
            title = item.find('title').text.strip()
            title = re.sub(r'[‘’]', '\'', title)
            link = item.find('link').text.strip()
            description = self.preprocess_description(item.find('description').text)
            category = item.find('category').text.strip()
            publish_date = self.preprocess_publish_date(item.find('pubDate').text)
            image_url = item.find('media:content', namespaces)
            
            if(category != 'Pakistan'):
                continue
            
            if(image_url):
                image_url = image_url.get('url')
            else:
                image_url = None
            
            print("GET:" , link)
            
            news_articles.append({
                "title":title , 
                "link" :link , 
                "news_category" : "pakistan",
                "publish_date":publish_date ,
                "scraped_date": datetime.now(),
                "source": self.source, 
                "image_url" : image_url,
                "clicks" : 0,
                "status" : "scraped",
                "blindspot" : False ,
                "content":description
                })
            
        return news_articles

    def scrape(self):
        try:
            print("Scraping " , self.source , " : \n") 
            xml_root = self.get_xml_root(self.rss_url)
            
            news_articles = self.extract_articles_from_xml(xml_root)
            latest_news_articles = self.filter_articles(news_articles)
            latest_news_articles = self.apply_NER(latest_news_articles)
            
            self.save_articles(latest_news_articles)
            
            print('Time : ' , datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
            print("\n\n")
        except Exception as e:
            print(f"Error Scraping {self.source} : " , e)
            