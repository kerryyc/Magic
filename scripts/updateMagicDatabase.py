from pymongo import MongoClient
from pprint import pprint
from pathlib import Path
from time import sleep
import requests
import os
import json

def getRequest(u):
    """ 
    Get request and sleep for 100 milliseconds 
    
    Args:
        u (str): url of request
    
    Returns:
        request: result of getting a request at the url
    """

    r = requests.get(url = u)
    sleep(0.1)
    return r

def openMongoDB(path):
    """
    Using the config file, open up the MongoDB database

    Args:
        path (Path): path to the parent directory where config.json is stored

    Returns:
        db (MongoClient.database_name): returns the main database 
    """
    # read config file to get username and password to access MongoDB
    with open(str(path.parent) + '\\config.json') as f:
        data = json.load(f)
        user = data['mongodb']['user']
        password = data['mongodb']['password']

    # access MongoDB cluster and Magic database
    client = MongoClient("mongodb+srv://" + user + ":" + password + "@cluster0-og8a0.mongodb.net/test?retryWrites=true&w=majority")
    db = client.magic
    return db

def addCardsToDatabase(db, magicSets):
    """
    Parse through all cards in the specified Magic sets from Scryfall API and add to the database

    Args:
        db (MongoClient.db_name.collection): MongoDB collection to store cards
        magicSets ([str]): array of Magic sets to get cards from

    Attributes:
        gAttributes ([str]): array of attributes that are guaranteed to appear in the Scryfall API response
        pAttributes ([str]): array of attirubtes that might be null or empty in the Scryfall API response  
    """

    gAttributes = ['name', 'foil', 'rulings_uri', 'cmc', 'color_identity', 'legalities', 'type_line', 'prices', 'rarity', 'set_name', 'set', 'textless']
    pAttributes = ['mana_cost', 'all_parts', 'card_faces', 'colors', 'loyalty', 'oracle_text', 'power', 'toughness', 'artist', 'flavor_text', 'image_uris']
    URI = 'https://api.scryfall.com/sets/'

    for mSet in magicSets:
        print('Parsing Set %s' % mSet)
        r = getRequest(getRequest((URI + mSet)).json()['search_uri'])
        data = r.json()
        while True:
            for c in data['data']:
                # if the card exists in the database already, skip it
                if db.count_documents({'card_id' : c['id']}, limit = 1) != 0:
                    print(c['name'] + ' already in DB')
                    continue

                card = {'card_id' : c['id']}

                # update card with attributes guaranteed to show up in the JSON response
                for a in gAttributes:
                    card.update({a : c[a]})
                
                # update card with attributes that can be null or missing from the JSON response
                for a in pAttributes:
                    if a in c:

                        # if the attribute is a card face, add only specific parts of that card face
                        if a == 'card_faces':
                            card.update({a : []})
                            for cf in c[a]:
                                card_face = {
                                    'name' : cf['name'],
                                    'mana_cost' : cf['mana_cost'],
                                    'type_line' : cf['type_line']
                                }
                                for cf_a in pAttributes:
                                    if cf_a in cf:
                                        card_face.update({cf_a : cf[cf_a]})

                                card[a].append(card_face)
                        
                        else:
                            card.update({a : c[a]})
                    
                try:
                    result = db.insert_one(card)
                    print('%s (%s) added' % (card['name'], card['card_id']))
                except Exception as exc: 
                    errorLogFile.write('%s/%s: %s\n' % (mSet, c['id'], str(exc)))
                    print('Error adding %s from %s' % (c['id'], mSet))

            if not data['has_more']:
                print()
                break        
            data = getRequest(data['next_page']).json()


if __name__ == '__main__':
    path = Path(os.path.dirname(os.path.abspath(__file__)))
    magicSets = ['thb', 'ptg', 'eld', 'm20', 'mh1', 'war', 'rna', 'uma', 'grn', 'm19', 'dom', 'a25', 'rix', 'e02', 'xln', 'hou', 'akh']

    # create error log file
    errorLogFile = open(str(path) + "\\errorlog.txt", "w")
    print('Created Error Log')

    # open DB for all magic cards
    db = openMongoDB(path).all # open magic.all collection
    print('Opened DB')

    # add all cards from magicSets to DB
    addCardsToDatabase(db, magicSets)

    print('Finished')
    errorLogFile.close()