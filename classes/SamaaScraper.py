from classes.PlaywrightScrapper import PlaywrightScrapper
from datetime import datetime , timedelta
from bs4 import BeautifulSoup

class SamaaScraper(PlaywrightScrapper):
    
    def __init__(self , rss_url="https://samaa.tv/pakistan" , source="Samaa_TV"):
        super().__init__(rss_url , source)
        return None
    
    def preprocess_publish_date(self , date):
        try:
            date_format = "%B %d, %Y"
            parsed_date = datetime.strptime(date , date_format)

            return parsed_date
        except Exception as e:
            return datetime.now()
    
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
            print("PARSED LINKS : " , articles)
            return articles
            
        except Exception as e:
            print("ERROR : error parsing article links")
            print(e)
            return None
        
    def parse_html_content(self , page):
        
        try:
            print("hey man we be parsing html content : " , page)
            page_content = BeautifulSoup(page , 'html.parser')
            main_article = page_content.find("article" , class_ = "single-article")
            print("main article : " , main_article.name)
            allowed_tags = set(['p','ul','li','h1','h2','h3','h4','h5','h6'])
            
            published_date = main_article.select(".share-bar time").text if main_article.select(".share-bar time") is not None else None
            published_date = self.preprocess_publish_date(published_date)
            
            print("published date : " , published_date)
            # image_url = main_article.find(".img-frame")
            # image_url = image_url['src'] if image_url is not None else None
            
            # content = ""
            # content_area_tags = main_article.find(".article-content")
            # print("here goes nothing  : "  , main_article.find(".article-content").text )
            # for tag in content_area_tags.children:
                
            #     if(tag.name in allowed_tags):
            #         content += tag.text + "\n"
            
            # print('Article Content : ' , content)
            
            # return {
            #     'content' : content,
            #     'news_category' : 'pakistan',
            #     'published_date' : published_date,
            #     'scraped_date' : datetime.now(),
            #     'source' : self.source,
            #     'image_url' : image_url,
            #     'status' : 'scraped',
            #     'clicks' : 0,
            #     'blindspot' : False
            # }
      
        except Exception as e:
            print(f"Error parsing html content for {self.source} ")
            print(e)
            raise Exception(f"Error parsing html content for {self.source} ")
        
        
    def scrape(self):
        
        html_page = self.get_html_page()
        article_links = self.parse_article_links(html_page)
        print("parsed articles ===> " , len(article_links))
        latest_articles = self.filter_articles(article_links)
        print("filtered articles ===> " , len(latest_articles))
        latest_articles = self.apply_NER(latest_articles)
        latest_articles = self.scrape_article_content(latest_articles , self.parse_html_content)
        print(latest_articles)
        
        
