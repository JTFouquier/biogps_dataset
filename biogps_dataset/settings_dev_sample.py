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

CACHE_HTTP_DATA = False

#dataset mining takes long time, debug mode may leak memory
#set False then
DEBUG = True

DEFAULT_GENE_ID = 1017
