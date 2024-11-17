from pymongo import MongoClient
import spacy

# Connect to MongoDB
client = MongoClient("mongodb+srv://admin:adminpassword@neutranews.h6vja.mongodb.net/?retryWrites=true&w=majority&appName=NeutraNews")
db = client.neutra_news
nlp = spacy.load("en_core_web_trf" , disable=['tagger' , 'parser' , 'lemmatizer'])

def apply_NER(articles):
    
    ner_labels = [
    "PERSON",      # People, including fictional
    "NORP",        # Nationalities or religious or political groups
    "FAC",         # Buildings, airports, highways, bridges, etc.
    "ORG",         # Companies, agencies, institutions, etc.
    "GPE",         # Countries, cities, states
    "LOC",         # Non-GPE locations, mountain ranges, bodies of water
    "PRODUCT",     # Objects, vehicles, foods, etc. (Not services)
    "EVENT",       # Named hurricanes, battles, wars, sports events, etc.
    "WORK_OF_ART", # Titles of books, songs, etc.
    "LAW",         # Named documents made into laws
    "LANGUAGE",    # Any named language
    ]

    for article in articles:
        doc = nlp(article['title'])
        
        entities = {}
        for ent in doc.ents:
            
            if ( ent.label_ not in ner_labels ): continue
            
            entity_text = ent.text.upper()
            if ent.label_ in entities:
                entities[ent.label_].append(entity_text)
            else:
                entities[ent.label_] = [entity_text]
                
        article['entities'] = entities
            
        print("Title : " , article['title'])
        print("entities : " , entities)
        print("\n\n")
        
    return articles

def apply_ner_to_bulk():
    
    collection = db['news_articles']
    documents = list(collection.find())
    documents = apply_NER(documents)
    
    for doc in documents:
        collection.update_one({"_id" : doc["_id"]} , {"$set" : doc})
    
    
    
apply_ner_to_bulk()


