# put your local settings here, like DB config
# and others
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    # DB for this project
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    # DB to retrive default dataset
    'default_ds': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'xxxx',
        'USER': 'xxxxxx',
        'PASSWORD': '',
        'HOST': 'xxx.xxx.xxx.xxx',
        'PORT': '5432',
    }
}

# weather cache http responses when fetch data
# used in ds load
CACHE_HTTP_DATA = False

# dataset mining takes long time, debug mode may leak memory
# set False then
DEBUG = True

# default gene id
DEFAULT_GENE_ID = 1017

# gene taxid, dataset default id mapping
DEFAULT_DATASET_MAPPING = {
    # human
    9606: 'E-GEOD-28079',
    # mouse
    10090: 'BDS_00002',
    # rat
    10116: 'GSE952',
    # fruit fly
    7227: 'X-XXXX-XXXX',
    # nematode
    6239: 'X-XXXX-XXXX',
    # zebrafish
    7955: 'X-XXXX-XXXX',
    # thale-cress
    3702: 'X-XXXX-XXXX',
    # frog
    8364: 'X-XXXX-XXXX',
    # pig
    9823: 'X-XXXX-XXXX',
}

DEFAULT_DS_ACCESSION = [u'BDS_00001', u'BDS_00002', u'BDS_00003', u'BDS_00004',
                        u'BDS_00005', u'BDS_00006', u'BDS_00007', u'BDS_00008',
                        u'BDS_00009', u'GSE10246', u'GSE952', u'GSE1133',
                        u'BDS_00010', u'BDS_00011', u'BDS_00012', u'BDS_00013',
                        u'BDS_00014']
