# -*-coding: utf-8 -*-
import json
from io import BytesIO

import pandas as pd
import numpy as np

from dataset import models
from django.core.management.base import BaseCommand
from django.conf import settings


"""Parsing user supplied information:

INFO SHEET:

An information sheet will need to be filled out by dataset owner, we provide
this sheet in a specific format. MUST ADD text to blank fields.

METADATA SHEET:

"factors" are where sample name and detailed information goes about every
sample. This comes from a user's metadata sheet in a tab-delimited text file.

NOTE/IMPORTANT: The fourth column (line[3].strip() below) MUST contain replicate information.
  ie. biological replicates will have the same name or condition. This can also be their name or
  if there are no biological replicates for samples. This is needed for averaging, as well as display names.
"""

"""
# we provide the info sheet for users to fill out
# from data load folder:
info_sheet = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_load/info_sheet.txt'
metadata_file = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_load/sheep_atlas_metadata.txt'

# from data output folder:
# NOTE, this file can be ouput from reporter_to_enrezgene.py or RNAseq data already containing Entrezgene IDs.
rnaseq_data_fixed_reporters = '/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/local_data_output/rnaseq_data_fixed_reporters.txt'
"""

class Command(BaseCommand):

    def handle(self, *args, **options):

        def parse_info_sheet(info_sheet):
            """This is an information sheet given to users in order to obtain
            info about their sequencing run.
            """
            print('Parse user-supplied info sheet & metadata sheet')
            print('STEP 1: START')
            print('STEP 1: parse information sheet from user')
            df = pd.read_table(info_sheet, sep='\t')
            # set the index to the info names; easier to parse
            df.index = df['info']

            df["info"] = df["info"].map(str.strip)

            info_dict = {
                'name': df.loc['name']['description'],
                'summary': df.loc['summary']['description'],
                'owner': df.loc['owner']['description'],
                'species': df.loc['species']['description'],
                'pubmed_id': df.loc['pubmed_id']['description'],
                'geo_gpl_id': df.loc['geo_gpl_id']['description'],
                'geo_gds_id': df.loc['geo_gds_id']['description'],
                'geo_gse_id': df.loc['geo_gse_id']['description'],
                'secondaryaccession': df.loc['secondaryaccession']['description']
            }
            print('STEP 1: END\n')
            return info_dict

        def create_factors_metadata_json(metadata_file):
            """Create the "factors" section which has information or "comments"
            about the samples.

            RNA sequence metadata file:

            MUST be a tab delimited .txt file, that contains
            an index column (i.e. numbers for each row, starting with 1,
            and not including the header row).

            All column titles/headers must be named uniquely.
            """
            print('STEP 2: START')
            print('STEP 2: "create factors" for meta, using metadata file '
                  'from user')
            lines = []
            with open(metadata_file, 'U') as metadata_file:
                for line in metadata_file:
                    new_line = line.strip().split('\t')
                    lines.append(new_line)

            factor_list = []
            column_name_list = lines[0]

            color_order_id = 1
            condition_previous = ""
            for line in lines[1:]:

                small_json_data = {}
                condition = line[3].strip()

                # If the condition is the same as the other condition, then color_order_id is the same
                # IMPORTANT, this assumes that there are two biological replicates. This may vary.
                if condition_previous == condition:
                    color_order_id += -1
                condition_previous = condition

                column_id = 1
                for column_name in column_name_list:
                    small_json_data[column_name] = line[column_id].strip()
                    column_id += 1

                large_json_data = {condition: {"factorvalue": small_json_data, "order_idx": color_order_id,
                                               "color_idx": color_order_id, "title": condition}}
                factor_list.append(large_json_data)
                color_order_id += 1

            print('STEP 2: END\n')

            return factor_list

        def fill_in_metadata(info_dict, factors):
            print('STEP 3: START')
            print('STEP 3: fill in meta for database data information')

            # metadata includes items from metadata sheet AND user info sheet
            metadata = {
                'geo_gds_id': info_dict['geo_gds_id'],
                'name': info_dict['name'],
                'default': False,
                'summary': info_dict['summary'],
                'geo_gse_id': info_dict['geo_gse_id'],
                'pubmed_id': info_dict['pubmed_id'],
                'owner': info_dict['owner'],
                'geo_gpl_id': info_dict['geo_gpl_id'],
                'secondaryaccession': info_dict['secondaryaccession'],
                'factors': factors
            }
            print('STEP 3: END\n')

            return metadata

        def create_biogps_dataset(rnaseq_data, info_dict, metadata):
            print('STEP 4: START')
            print('STEP 4: Create BioGPS "dataset" object, "dataset data" object, '
                  'and "dataset matrix" object')
            sample_count = len(metadata['factors'])
            print('STEP 4: dataset sample count: ' + str(sample_count))

            factor_data = metadata

            final_factor_list = []
            for d in factor_data['factors']:
                final_factor_list.append(list(d.values())[0]['factorvalue'])

            final_factors = json.dumps(final_factor_list)

            if models.BiogpsDataset.objects.filter(name=info_dict['name']):
                print('STEP 4: Dataset already created, script terminated. To rerun'
                      'dataset load, delete the dataset first in shell_plus')

                return

            else:
                models.BiogpsDataset.objects.create(name=info_dict['name'],
                                                    summary=info_dict['summary'],
                                                    ownerprofile_id=info_dict['owner'],
                                                    platform=models.BiogpsDatasetPlatform.objects.all().first(),
                                                    geo_gds_id=info_dict['geo_gds_id'],
                                                    geo_gse_id=info_dict['geo_gse_id'],
                                                    geo_id_plat=info_dict['geo_gpl_id'],
                                                    metadata=metadata,
                                                    species=info_dict['species'],
                                                    sample_count=sample_count,
                                                    factor_count=len(final_factor_list[0]),
                                                    factors=final_factors,
                                                    pop_total=0
                                                    )
            dataset = models.BiogpsDataset.objects.get(name=info_dict['name'])
            # For logging purposes:
            print('STEP 4: dataset instance: ' + str(dataset))
            print('STEP 4: dataset.id: ' + str(dataset.id))
            print('STEP 4: dataset.name: ' + str(dataset.name))

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
            print('STEP 4: END')

        def main(rnaseq_data_fixed_reporters, info_sheet, metadata_file):
            info_dict = parse_info_sheet(info_sheet)
            factors = create_factors_metadata_json(metadata_file)
            metadata = fill_in_metadata(info_dict, factors)
            create_biogps_dataset(rnaseq_data_fixed_reporters, info_dict, metadata)

        """
        Below is an example of how you would call this sheet using the rnaseq_data_fixed_reporters which comes
        from reporter_to_entrezgene.py helper file, and the metadata and info sheet.
        If your RNAseq data file already contains Entrezgene IDs, then no need to run the helper file.
        """

        # main(rnaseq_data_fixed_reporters, info_sheet, metadata_file)