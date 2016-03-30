"""
Django settings for biogps_dataset project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dataset',

    'grappelli',
    'django.contrib.admin',
    'django_extensions',
    'tagging',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'biogps_dataset.urls'

WSGI_APPLICATION = 'biogps_dataset.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


CACHES = {
    'default': {
        # 'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(os.path.dirname(__file__), "../static/")

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), '../web/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


##################################################
# The following are the app-specific settings
##################################################

#used by load_ds management command
CACHE_HTTP_DATA = False
#default gene id
DEFAULT_GENE_ID = 1017

#gene taxid, dataset default id mapping
DEFAULT_DATASET_MAPPING = {
    # human
    9606: 'GSE1133',
    # mouse
    10090: 'GSE10246',
    # rat
    10116: 'GSE952',
    # fruit fly
    #7227: 10,
    # nematode
    #6239: 10,
    # zebrafish
    #7955: 10,
    # thale-cress
    #3702: 10,
    # frog
    #8364: 10,
    # pig
    9823: 'BDS_00012',
}

# DEFAULT_DS_TOKEN = ['GSE952', 'GSE10246']
# [ds.id for ds in BiogpsDataset.objects.all() if ds.metadata['default']]
# DEFAULT_DS_ID = [6, 8, 9, 10, 11, 12, 13, 14, 3, 4, 5, 1, 2428, 2, 2427, 2430, 7]
DEFAULT_DS_ACCESSION = ['BDS_00001', 'BDS_00002', 'BDS_00003', 'BDS_00004', 'BDS_00005', 'BDS_00006',
                        'BDS_00007', 'BDS_00008', 'BDS_00009', 'GSE10246', 'GSE952', 'GSE1133',
                        'BDS_00010', 'BDS_00011', 'BDS_00012', 'BDS_00013', 'BDS_00014']

MAX_SUPPORTED_SAMPLES = 1000
NCBO_ANNO_KEY = '055e682a-0ea9-4f3c-af0d-4e8692d94bcf'
POPULAR_FACTORS = ['TREATMENT', 'GENOTYPE', 'CELL TYPE', 'AGE', 'CELL LINE', 'ORGANISM PART',
                   'TIME', 'SEX', 'genotype', 'VARIATION', 'compound', 'TISSUE', 'Compound',
                   'COMPOUND', 'GENOTYPE/VARIATION', 'DISEASE STATE', 'time', 'dose', 'STRAIN',
                   'GENDER', 'Time', 'Genotype', 'disease state', 'AGENT', 'DiseaseState',
                   'STRAIN OR LINE', 'DOSE', 'cell type', 'TRANSFECTION', 'DEVELOPMENTAL STAGE',
                   'PHENOTYPE', 'PROTOCOL', 'disease', 'growth condition', 'INFECTION', 'OrganismPart',
                   'SAMPLE TYPE', 'INDIVIDUAL', 'DIET', 'DISEASE STATUS', 'organism part', 'cell line',
                   'Age', 'CellType', 'CHIP ANTIBODY', 'Dose', 'clinical information', 'CONDITION',
                   'PATIENT', 'STAGE', 'Treatment', 'TIME POINT', 'TREATED WITH', 'TISSUE TYPE', 'GROUP',
                   'GrowthCondition', 'Individual', 'DISEASE_STATE', 'StrainOrLine', 'REPLICATE', 'HISTOLOGY',
                   'GRADE', 'SUBJECT', 'ANTIBODY', 'SIRNA', 'RNAi', 'PASSAGE', 'DIAGNOSIS', 'infect', 'age',
                   'CellLine', 'CELL POPULATION', 'TREATMENT GROUP', 'DevelopmentalStage', 'BIOSOURCEPROVIDER',
                   'KNOCKDOWN', 'phenotype', 'STATUS', 'DISEASE', 'STRESS', 'Phenotype', 'Sex', 'treatment',
                   'SAMPLE ID', 'TRANSDUCTION', 'CELL_TYPE', 'DONOR', 'developmental stage', 'GeneticModification',
                   'strain', 'diet', 'GENETIC BACKGROUND', 'ETHNICITY', 'CONCENTRATION', 'EnvironmentalStress',
                   'RNA interference', 'CULTURE CONDITION', 'TUMOR STAGE', 'SAMPLE', 'BATCH', 'GENOME/VARIATION',
                   'BIOLOGICAL REPLICATE', 'RACE', 'SMOKING STATUS', 'ORGANISM_PART', 'DISEASESTATE',
                   'TREATMENT DURATION', 'PATIENT IDENTIFIER', 'TYPE', 'STIMULATION', 'PATIENT ID', 'SHRNA',
                   'ClinicalInformation', 'KARYOTYPE', 'SAMPLE GROUP', 'ORIGIN', 'SUBTYPE', 'ClinicalTreatment', 'TRANSGENE']


MAX_SAMPLE_4_CORRELATION = 400   # 200


ES_URLS = {
    'BGPS': "http://localhost:9200/biogps_ds/",
    'PF_C': "http://localhost:9200/biogps_ds/platform/_mapping",
    'DS_C': "http://localhost:9200/biogps_ds/dataset/_mapping",
    'PF': "http://localhost:9200/biogps_ds/platform/",
    'DS': "http://localhost:9200/biogps_ds/dataset/",
    'SCH': "http://localhost:9200/biogps_ds/dataset/_search",
}

# DEFAULT_DS_TOKEN = ['GSE952', 'GSE10246']
# [ds.id for ds in BiogpsDataset.objects.all() if ds.metadata['default']]
DEFAULT_DS_ID = [6, 8, 9, 10, 11, 12, 13, 14, 3, 4, 5, 1, 2428,
                 2, 2427, 2430, 7]

BAR_COLORS = ['#9400D3', '#2F4F4F', '#483D8B', '#8FBC8B', '#E9967A', '#8B0000',
              '#9932CC', '#FF8C00', '#556B2F', '#8B008B', '#BDB76B', '#7FFFD4',
              '#A9A9A9', '#B8860B', '#008B8B', '#00008B', '#00FFFF', '#DC143C',
              '#6495ED', '#FF7F50', '#D2691E', '#7FFF00', '#5F9EA0', '#DEB887',
              '#A52A2A', '#8A2BE2', '#0000FF', '#000000', '#FFE4C4', '#006400',
              '#00FFFF']
