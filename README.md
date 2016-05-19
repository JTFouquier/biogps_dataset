
## Detailed steps needed to have a local development version of [BioGPS](http://biogps.org/#goto=welcome), for dataset loading


## Setting up your local development environment:

Make sure you use git for version control (May 2016 Biogps_dataset was migrated to Github)

### Make virtual environment and clone repository (use your Github username of course!)

- `git clone https://github.com/JTFouquier/biogps_dataset.git`
- `virtualenv biogps`
- `source biogps/bin/activate`
- `pip install -r requirements.txt`

### Install Elastic Search using the following directions:

#### Elastic search is a search server based on Lucene. It provides a distributed, multitenant-capable full-text search engine with an HTTP web interface and schema-free JSON documents.
#### Elastic search is developed in Java and is released as open source under the terms of the Apache License.

[Elastic Search installation instructions](https://www.astic.co/guide/en/elasticsearch/reference/current/_installation.html)

# You must have three main components running in order to see data inside your dev/local version of BioGPS

### 1) SSH into the remote BioGPS dataset
#### Because the dataset database is much too large to install on computer for local development, you need to request a connection to our dev db server

### 2) Run the local host server

The settings_dev file is a "secret file." Please see Chunlei or BioGPS project manager

- `python3 manage.py runserver_plus --settings=biogps_dataset.settings_dev`

### 3) Run Elastic Search

#### From within the elasticsearch folder that you set up, run:

- `./bin/elasticsearch`

## Get data from a BioGPS user/researcher
### You will need to get an information sheet, metadata sheet and RNAseq data/matrix file from a scientist.

### Does the local dataset you are loading have gene symbols in it?
#### If yes, then you MUST run reporter_to_entrezgene.py, which will use mygene.info to replace gene symbols with entrezgene IDs.

#### Entrezgene IDs are absolutely necessary for Biogps.org data display.

## Dataset Parsers:

#### load_ds script which will load *remote* data to remote server for dev or prod. (Microarray data)
#### load_ds_local script will load *local* data to the remote server for dev or prod. (written for RNAseq)

### Run the command like this, where "load_ds_local" can be other commands

- `python3 manage.py load_ds_local --settings=biogps_dataset.settings_dev`

### Then you must use the command es_index to "index the data", then newly loaded data should appear in the chart file.

#### index the dataset (more explanation between this and load)
- `python3 manage.py es_index --settings=biogps_dataset.settings_dev`

#### Output looks something like this:
added 16 platform, added 5914 dataset (example of output)

## Open this url and you should see bar charts!
#### http://localhost:8000/static/data_chart.html

*Must sometimes restart the localhost and server that is containing the database, as well as elasticsearch.*

**For help:**
- `python3 manage.py load_ds -help --settings=biogps_dataset.settings_dev`

## Instances (models) to create during data load:
#### P.S. If you don't know what a model is, then read about [Django](https://www.djangoproject.com/)!

* **dataset:**
    * Model with information about a certain dataset including metadata.

* **dataset_matrix:**

    * is the data matrix that contains *all* of the data from the RNA seq run. Meaning, you likely do not want to display an instance of this model all at once!

* **dataset_data:**
    * is one reporter gene, and all of it's expression information for all samples.

* **Dataset Platform:**
    * We created a new platform since now we're loading sequencing (not microarray) data.
This is a sequencing platform, so does not have to be recreated every time.

    * Example input information:
        * RNA seq
        * reporters empty list
        * name = "generic RNA seq platform for mouse"
        * species = mouse


#### Biogps takes the average of samples for you so you don't need user average

### Misc. information for testing/developing BioGPS:

symbol examples from mygene.info used to get the Entrezgene IDs inside the helper file:

- `http://mygene.info/v2/query?q=symbol:0610005C13Rik`
- `http://mygene.info/v2/query?q=symbol:42430`

## To access code via the shell inside the Django project, run:
- `python manage.py shell_plus --settings=biogps_dataset.settings_dev`

#### Run these commands from shell:

This returns the dataset object which is the foreign key for dataset data and dataset matrix:

ds = BiogpsDataset.objects.get(name='Transient overexpression of transcription factor pairs generate functional induced neurons directly from mouse embryonic fibroblasts.')


## Testing that charts are visible on your BioGPS localhost

Dropdown menu in "probeset" is also considered the reporter gene on BioGPS

Go to the URL for the specific gene and dataset name (primary key of dataset or geo_gse_id)
geo_gse_id is also important: will be BDS_XXXXX next number in sequence)

Examples
- `http://localhost:8000/static/data_chart.html?gene=67669&dataset=10044`
- `http://localhost:8000/static/data_chart.html?gene=12566&dataset=10044`
- `http://localhost:8000/static/data_chart.html?gene=100152011&dataset=10078`
- `http://localhost:8000/admin/dataset/biogpsdataset/2427/`

Standard test gene is 1017, which is a *human* gene! So if you are using mouse
data, this will understandably be missing:

CDK2 cyclin-dependent kinase 2, Homo sapiens (human)
Gene ID: 1017, updated on 6-Mar-2016

Cdk2 cyclin-dependent kinase 2, Mus musculus (house mouse)
Gene ID: 12566, updated on 6-Mar-2016

You can also check the "fixed reporters" data file to see which Entrezgene IDs are actually in your dataset for
viewing.

## To view the full data for a dataset and gene:
- `http://localhost:8000/dataset/full-data/geo_gse_id%20test/gene/12566/`
- `http://localhost:8000/dataset/full-data/E-GEOD-16054/gene/1017/`
- `http://localhost:8000/dataset/full-data/BDS_00001/gene/1017/`

#### Does your dataset have interesting tissue groups or organ systems? If so, then change the color_idx in the json metadata (ex: admin/dataset/biogpsdataset/2509/) accordingly to group samples into meaningful groups. This is done manually due to the numerous variations of possible sample groupings


