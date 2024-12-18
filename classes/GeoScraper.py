import re
from classes.Scraper import Scraper
from datetime import datetime

class GeoScraper(Scraper):

    def __init__(self , rss_url = "https://feeds.feedburner.com/geo/GiKR", source='Geo'):
        super().__init__( rss_url, source)  
        return None

    def extract_articles_from_xml(self , root):
    
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
                "source": self.source,
                "news_category": "pakistan",
                "blindspot" : False ,
                "status" : "scraped",
                "clicks" : 0
                })
            
        return news_articles

    def parse_html_content(self , page):
        
        try:
            content_area = page.find('div' , class_="content-area")

            if(not content_area):
                content_area = page.find('div' , class_="long-content")

            content_area_paragraphs = content_area.findAll('p')
            content_area_text = [ paragraph.text for paragraph in content_area_paragraphs]
            content_area_text = " ".join(content_area_text)
            content_area_text = self.clean_text(content_area_text)
            
        except Exception as e:
            print("Error while parsing HTML content : " , e)
            return None
            
        return content_area_text

    def scrape(self):
        try:
            print("Scraping " , self.source , " : \n") 
            xml_root = self.get_xml_root(self.rss_url)

            news_articles = self.extract_articles_from_xml(xml_root)
            latest_news_articles = self.filter_articles(news_articles)
            latest_news_articles = self.apply_NER(latest_news_articles)
            scraped_news_articles = self.scrape_article_content( latest_news_articles ,self.parse_html_content )

            self.save_articles(scraped_news_articles)      
            print('Time : ' , datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
            print("\n\n")
            
        except Exception as e:
            print(f"Error scraping {self.source}  : " , e)
            