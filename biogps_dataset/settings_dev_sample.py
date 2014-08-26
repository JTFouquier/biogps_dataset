#put your local settings here, like DB config
#and others
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

#if cache http responses when fetch data
#used in ds load
CACHE_HTTP_DATA = False

#dataset mining takes long time, debug mode may leak memory
#set False then
DEBUG = True

#default gene id
DEFAULT_GENE_ID = 1017

#gene taxid, dataset default id mapping
DEFAULT_DATASET_MAPPING = {
    # human
    9606: 10,
    # mouse
    10090: 10,
    # rat
    10116: 10,
    # fruit fly
    7227: 10,
    # nematode
    6239: 10,
    # zebrafish
    7955: 10,
    # thale-cress
    3702: 10,
    # frog
    8364: 10,
    # pig
    9823: 10,
}

