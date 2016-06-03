# -*-coding: utf-8 -*-
from io import BytesIO

import pandas as pd
import numpy as np

from dataset import models
from django.core.management.base import BaseCommand

"""Parsing user supplied information:

1) INFO SHEET:

An information sheet will need to be filled out by dataset owner, we provide
this sheet in a specific format. MUST ADD text to blank fields.

2) FACTORS SHEET:

"factors" are where sample name and detailed information goes about every
sample. This comes from a user's factor sheet in a tab-delimited text file.

NOTE/IMPORTANT: The fourth column (line[3].strip() below) MUST contain replicate
  information. ie. biological replicates will have the same name or condition.
  This can also be their name or if there are no biological replicates for samples.
  This is needed for averaging, as well as display names.

3) DATA SHEET:

The data is where the gene expression information is found. The sample names must
be in the top/header row of the data sheet and the 2nd column of the factors sheet.

SEE EXAMPLES in data_load_small_examples to make sure your files are
preprocessed correctly
"""

"""
# from local_data_load folder:
info_sheet = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_load/info_sheet.txt'
factors_file = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_load/sheep_atlas_factors.txt'

# From local_data_output folder:
# NOTE, this file can be ouput from reporter_to_enrezgene.py or RNAseq data
# already containing Entrezgene IDs.
# rnaseq_data_fixed_reporters = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_output/rnaseq_data_fixed_reporters.txt'
# version using ensembl ID, which was not run through reporter_to_entrezgene.py (no need for this DS):
rnaseq_data_fixed_reporters = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_load/sheep_atlas_ensembl.txt'

# This platform id must be entered by developer after manually determining
# which platform is correct, OR after you
# create the appropriate platform.
seq_platform_id = '16'
"""


class Command(BaseCommand):

    def handle(self, *args, **options):

        def parse_info_sheet(info_sheet):
            """This is an information sheet given to users in order to obtain
            info about their sequencing run.
            """
            print('Parse user-supplied info sheet & factors sheet')
            print('STEP 1: START')
            print('STEP 1: parse information sheet from user')
            df = pd.read_table(info_sheet, sep='\t')
            # replace nans with strings
            df = df.fillna('unknown')
            # set the index to the info names; easier to parse
            df.index = df['info']

            df["info"] = df["info"].map(str.strip)

            def _make_new_geo_gse_id():
                # istartswith is case insensitive filter option in Django
                datasets = models.BiogpsDataset.objects.filter(geo_gse_id__istartswith="BDS")

                id_list = []
                for ds in datasets:
                    id_list.append(ds.geo_gse_id)

                old_gse_number = max(id_list)
                _, old_gse_number = old_gse_number.split('_')
                new_gse_number = int(old_gse_number) + 1
                new_gse_string = 'BDS_' + (str(new_gse_number)).zfill(5)

                return new_gse_string

            metadata_dict = {
                'name': df.loc['name']['description'],
                'summary': df.loc['summary']['description'],
                'owner': df.loc['owner']['description'],
                'species': df.loc['species']['description'],
                'pubmed_id': df.loc['pubmed_id']['description'],
                'geo_gpl_id': df.loc['geo_gpl_id']['description'],
                'geo_gds_id': df.loc['geo_gds_id']['description'],
                'geo_gse_id': _make_new_geo_gse_id(),
                'secondaryaccession': df.loc['secondaryaccession']['description']
            }
            print('STEP 1: END\n')
            return metadata_dict

        def create_factors_metadata_json(factors_file):
            """Create the "factors" section which has information or "comments"
            about the samples.

            RNAseq factors file:

            MUST be a tab delimited .txt file, that contains
            an index column (i.e. numbers for each row, starting with 1,
            and not including the header row).

            All column titles/headers must be named uniquely.
            """
            print('STEP 2: START')
            print('STEP 2: "create factors" for meta, using factors file from user')
            lines = []
            with open(factors_file, 'U') as factors_file:
                for line in factors_file:
                    new_line = line.strip().split('\t')
                    lines.append(new_line)

            factor_list = []
            column_name_list = lines[0]
            # sort by condition/biological replicate
            sorted(lines, key=lambda x: x[3])
            color_order_id = 1
            condition_previous = ""
            for line in lines[1:]:

                small_json_data = {}
                condition = line[3].strip()

                # If the condition is the same as the other condition,
                # then color_order_id is the same
                # IMPORTANT, this assumes that there are zero or two biological replicates.
                # This may vary.
                if condition_previous == condition:
                    color_order_id += -1
                condition_previous = condition

                column_id = 1
                for column_name in column_name_list:
                    small_json_data[column_name] = line[column_id].strip()
                    column_id += 1

                large_json_data = {condition:
                                   {"factorvalue": small_json_data,
                                    "order_idx": color_order_id,
                                    "color_idx": color_order_id,
                                    "title": condition}
                                   }
                factor_list.append(large_json_data)
                color_order_id += 1

            print('STEP 2: END\n')

            return factor_list

        def fill_in_metadata(metadata_dict, factors):
            print('STEP 3: START')
            print('STEP 3: fill in meta for database data information')

            # metadata includes items from metadata sheet AND user info sheet
            metadata = {
                'geo_gds_id': metadata_dict['geo_gds_id'],
                'name': metadata_dict['name'],
                'default': False,
                'summary': metadata_dict['summary'],
                'geo_gse_id': metadata_dict['geo_gse_id'],
                'pubmed_id': metadata_dict['pubmed_id'],
                'owner': metadata_dict['owner'],
                'geo_gpl_id': metadata_dict['geo_gpl_id'],
                'secondaryaccession': metadata_dict['secondaryaccession'],
                'factors': factors
            }
            print('STEP 3: END\n')

            return metadata

        def create_biogps_dataset(rnaseq_data, metadata_dict, metadata, seq_platform_id):
            print('STEP 4: START')
            print('STEP 4: Create BioGPS "dataset" object, "dataset data" object, '
                  'and "dataset matrix" object')
            sample_count = len(metadata['factors'])
            print('STEP 4: dataset sample count: ' + str(sample_count))

            factor_data = metadata

            final_factors = []
            for d in factor_data['factors']:
                final_factors.append(list(d.values())[0]['factorvalue'])

            if models.BiogpsDataset.objects.filter(name=metadata_dict['name']):
                print('STEP 4: Dataset already created, script terminated. To rerun'
                      'dataset load, delete the dataset first in shell_plus')

                return

            else:
                models.BiogpsDataset.objects.create(name=metadata_dict['name'],
                                                    summary=metadata_dict['summary'],
                                                    ownerprofile_id=metadata_dict['owner'],
                                                    platform=models.BiogpsDatasetPlatform.objects.get(id=seq_platform_id),
                                                    geo_gds_id=metadata_dict['geo_gds_id'],
                                                    geo_gse_id=metadata_dict['geo_gse_id'],
                                                    geo_id_plat=metadata_dict['geo_gpl_id'],
                                                    metadata=metadata,
                                                    species=metadata_dict['species'],
                                                    sample_count=sample_count,
                                                    factor_count=len(final_factors[0]),
                                                    factors=final_factors,
                                                    pop_total=0
                                                    )
            dataset = models.BiogpsDataset.objects.get(geo_gse_id=metadata_dict['geo_gse_id'])
            # For logging purposes:
            print('STEP 4: dataset instance: ' + str(dataset))
            print('STEP 4: dataset.id: ' + str(dataset.id))
            print('STEP 4: dataset.name: ' + str(dataset.name))
            print('STEP 4: dataset.geo_gse_id: ' + str(dataset.geo_gse_id))

            dataframe = pd.read_csv(rnaseq_data, index_col=0, sep='\t')
            datasetdata = []
            for idx in dataframe.index:
                datasetdata.append(models.BiogpsDatasetData(dataset=dataset,
                                                            reporter=idx,
                                                            data=dataframe.loc[idx, :].values.tolist()))

            # create all the individual **DATA** items (BiogpsDatasetData)
            models.BiogpsDatasetData.objects.bulk_create(datasetdata)
            # create and save the **MATRIX** (BiogpsDatasetMatrix)
            # tmp file
            s = BytesIO()
            np.save(s, dataframe.values)
            s.seek(0)
            matrix = models.BiogpsDatasetMatrix(dataset=dataset,
                                                reporters=dataframe.index.tolist(),
                                                matrix=s.read())
            matrix.save()
            get_random_test_genes = models.BiogpsDatasetData.objects.filter(dataset=dataset)[0:5]
            print('STEP 4: test url: ' + 'http://localhost:8000/static/data_chart.html?gene=' +
                  str(get_random_test_genes[0].reporter) + '&dataset=' + str(dataset.geo_gse_id))

            gene_list = []
            for gene in get_random_test_genes:
                gene_list.append(str(gene.reporter))

            print('STEP 4: other genes to test: ' + str(gene_list))
            print('STEP 4: END')

        def main(rnaseq_data_fixed_reporters, info_sheet, factors_file,
                 seq_platform_id):
            metadata_dict = parse_info_sheet(info_sheet)
            factors = create_factors_metadata_json(factors_file)
            metadata = fill_in_metadata(metadata_dict, factors)
            create_biogps_dataset(rnaseq_data_fixed_reporters, metadata_dict,
                                  metadata, seq_platform_id)

        """
        Below is an example of how you would call this sheet using 1) rnaseq_data_fixed_reporters
        which comes from reporter_to_entrezgene.py helper file, and the 2) factors sheet and 3)
        info sheet. If your RNAseq dataset file already contains Entrezgene IDs or you are loading
        Microarray data, then no need to run reporter_to_entrezgene.py the helper file.
        """

        # main(rnaseq_data_fixed_reporters, info_sheet, factors_file, seq_platform_id)
