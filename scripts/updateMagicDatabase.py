from pymongo import MongoClient
from pprint import pprint
from pathlib import Path
from time import sleep
import requests
import os
import json

# read config file to get username and password to access MongoDB
path = Path(os.path.dirname(os.path.abspath(__file__)))
with open(str(path.parent) + '\\config.json') as f:
    data = json.load(f)
    user = data['mongodb']['user']
    password = data['mongodb']['password']

# create error log file
errorLogFile = open(str(path) + "\\errorlog.txt", "w")
print('Created Error Log')

# access MongoDB cluster and Magic database
client = MongoClient("mongodb+srv://" + user + ":" + password + "@cluster0-og8a0.mongodb.net/test?retryWrites=true&w=majority")
db = client.magic
print('Opened DB')

# parse through Scryfall API sets (no all cards due to limited database storage)
magicSets = ['thb', 'ptg', 'eld', 'm20', 'mh1', 'war', 'rna', 'uma', 'grn', 'm19', 'dom', 'a25', 'rix', 'e02', 'xln', 'hou', 'akh']
gAttributes = ['foil', 'rulings_uri', 'cmc', 'color_identity', 'legalities', 'mana_cost', 'name', 'type_line', 'prices', 'rarity', 'set_name', 'set', 'textless']
pAttributes = ['all_parts', 'card_faces', 'colors', 'loyalty', 'oracle_text', 'power', 'toughness', 'artist', 'flavor_text', 'image_uris']
URI = 'https://api.scryfall.com/sets/'
# for mSet in magicSets:
for mSet in ['eld']:
    print('Parsing Set %s' % mSet)
    r = requests.get(url = requests.get(url = URI + mSet).json()['search_uri'])
    data = r.json()
    while True:
        for c in data['data']:
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
                result = db.all.insert_one(card)
                print('%s (%s) added' % (card['name'], card['card_id']))
            except Exception as exc: 
                errorLogFile.write('%s/%s: %s\n' % (mSet, c['id'], str(exc)))
                print('Error adding %s from %s' % (c['id'], mSet))

        if not data['has_more']:
            break        
        sleep(0.1) # 100 millisecond delay before requesting from API
        data = requests.get(url = data['next_page']).json()

print('Finished')
errorLogFile.close()