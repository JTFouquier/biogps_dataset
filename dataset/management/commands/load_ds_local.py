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
this sheet in a specific format.

METADATA SHEET:

"factors" are where sample name and detailed information goes about every
sample. This comes from a user's metadata sheet in a tab-delimited text file.
"""

# we provide this sheet to them to fill out
info_sheet = '/Users/fouquier/repos/biogps_dataset/dataset/management/\
local_data_load/info_sheet.txt'
# this is the metadata file from the user
rna_seq_metadata_file = '/Users/fouquier/repos/biogps_dataset/dataset/\
management/local_data_load/Baldwin-Metadata-InducedNeurons.txt'


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
                # (TODO) what is this
                'secondaryaccession': df.loc['secondaryaccession']['description']
            }
            print('STEP 1: END')
            return info_dict

        def create_factors_metadata_json(rna_seq_metadata_file):
            """Create the "factors" section which has information or "comments"
            about the samples.

            RNA sequence metadata file:

            MUST be a tab delimited .txt file, that contains
            an index column (i.e. numbers for each row, starting with 1,
            and not including the header row).

            All column titles/headers must be named uniquely.
            """
            print('STEP 2: START')
            print('STEP 2: "create factors" for meta, using metadata file\
            from user')
            lines = []
            with open(rna_seq_metadata_file, 'U') as rna_seq_metadata_file:
                for line in rna_seq_metadata_file:
                    new_line = line.strip().split('\t')
                    lines.append(new_line)

            factor_list = []
            column_name_list = lines[0]

            for line in lines[1:]:

                small_json_data = {}
                # (TODO) confused about this and sample name.

                # In non average data file the names are A1-B2-3, not A1-B2
                # (TODO) working
                # sample_name = line[2].strip()  # THIS LINE WORKS
                # THIS LINE WORKS (TODO) this theoretically adds the condition
                sample_name = line[3].strip()

                column_id = 1
                for column_name in column_name_list:
                    small_json_data[column_name] = line[column_id].strip()
                    column_id += 1

                large_json_data = {sample_name: {'comment': small_json_data}}
                factor_list.append(large_json_data)

            print('STEP 2: END')
            fout = open('factor_meta_file_line_of_2_TEST.txt', 'w')
            fout.write(str(factor_list))
            fout.close()
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
            print('STEP 3: END')
            return metadata

        def create_biogps_dataset(info_dict, metadata):

            factors = metadata['factors']
            sample_count = len(factors)
            print('sample count', sample_count)
            factor_count = 0

            # (TODO) confused about this. this is from _exp_save,
            # where BiogpsDatasetData comes from
            # Why isn't it showing up
            fvs = []
            for e in factors:
                e = e[e.keys()[0]]
                if 'factorvalue' not in e:
                    break
                fvs.append(e['factorvalue'])
            if len(fvs) > 0:
                factor_count = len(fvs[0].keys())

            if models.BiogpsDataset.objects.filter(name=info_dict['name']):
                print('dataset already created, script terminated. To rerun\
                dataset load, delete the dataset first in shell_plus')
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
                                                    factor_count=factor_count,
                                                    factors=fvs,
                                                    pop_total=0
                                                    )
            dataset = models.BiogpsDataset.objects.get(name=info_dict['name'])
            print(dataset)
            print(dataset.id)
            print(dataset.name)

            dataframe = pd.read_csv('/Users/fouquier/repos/biogps_dataset/dataset/utils/helper_files/rnaseq_dataframe_file.txt', index_col=0, sep='\t')

            datasetdata = []
            for idx in dataframe.index:
                datasetdata.append(models.BiogpsDatasetData(dataset=dataset,
                                                            reporter=idx,
                                                            data=list(dataframe.loc[idx, :].values)))

            # create all the individual **DATA** items (BiogpsDatasetData)
            models.BiogpsDatasetData.objects.bulk_create(datasetdata)

            # create and save the **MATRIX** (BiogpsDatasetMatrix)
            # tmp file
            s = BytesIO()
            np.save(s, dataframe.values)
            s.seek(0)
            matrix = models.BiogpsDatasetMatrix(dataset=dataset,
                                                reporters=list(dataframe.index),
                                                matrix=s.read())
            matrix.save()


        def main():
            info_dict = parse_info_sheet(info_sheet)
            factors = create_factors_metadata_json(rna_seq_metadata_file)
            metadata = fill_in_metadata(info_dict, factors)
            create_biogps_dataset(info_dict, metadata)

        main()
