from classes.PlaywrightScrapper import PlaywrightScrapper
from datetime import datetime , timedelta

class SamaaScraper(PlaywrightScrapper):
    
    def __init__(self , rss_url="https://samaa.tv/pakistan" , source="Samaa_TV"):
        super().__init__(rss_url , source)
        return None
    
    def preprocess_publish_date(self , date):
        try:
            date_format = "%a, %d %b %Y %H:%M:%S %z"
            parsed_date = datetime.strptime(date , date_format)

            return parsed_date
        except Exception as e:
            print("failed to parse published time")
    
    def parse_article_links(self , html_page):
        try:
            articles = []
            article_tags = html_page.find_all("article")
            
            for i , article in enumerate(article_tags):

                article_title = article.find("h3").text
                article_link = article.find("a")['href'] 
                
                articles.append({
                    'title' : article_title,
                    'link' : article_link
                })
                
            return articles
            
        except Exception as e:
            print("ERROR : error parsing article links")
            print(e)
            return None
        
    def parse_html_content(self , page):
        
        try:
            published_date = page.find("time")
            content_area_paragraphs = page.find_all("div.article-content p")
            content_area_text = [ p.text for p in content_area_paragraphs ]
            content_area_text = " ".join(content_area_text)
            print('Article Content : ' , content_area_text)
            
            return {
                ''
            }
            pass
        except Exception as e:
            print('Error')
        
        
    def scrape(self):
        
        html_page = self.get_html_page()
        article_links = self.parse_article_links(html_page)
        latest_articles = self.filter_articles(article_links)
        latest_articles = self.apply_NER(latest_articles)
        print(latest_articles)
        
        
