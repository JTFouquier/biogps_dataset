
import pandas as pd

import mygene

"""
This is a helper file to return entrezgene IDs for BioGPS data loading. It is
not necessary to run on all datasets, only those datasets which use a reporter
type that is NOT Entrezgene ID.

Entrezgene ID AKA: NCBI gene IDs.

This specific helper file dataset was written for local RNAseq data for mouse.

BioGPS typically handles Microarray data and also handles dataloading
from remote data repositories (hosted online) and not local data.

The reporter genes provided for local datasets are
often the symbol which is not the correct format for BioGPS.
"""

# these 3 variables should be modified to the local dataset
species = 'mouse'
# if your reporters are symbols, keep this as 'symbol'
reporter_type = 'symbol'  # (TODO might not all be symbol)

input_seq_file = '/Users/fouquier/repos/biogps_dataset/dataset/management/\
local_data_load/2016.02.10_normalizedcounts_iNswithMEFs.txt'
# input_seq_file = 'iN_final_duplicates_normalizedcounts_avg.txt'
# (TODO) test other datasets.


def read_file_get_reporter_query_list(input_seq_file):
    """Take a users input file from their sequencing run and get a list of the
    reporter genes used. They should all be entrezgene IDs, but most are
    symbols. Attempt to find entrezgene IDs for reporters.
    """
    print("Step 1: START")
    print("Step 1: get reporter gene column as list from RNAseq run")

    df = pd.read_table(input_seq_file, sep='\t')
    reporter_query_list = df.ix[:, 0].tolist()
    print("Step 1: END")
    return reporter_query_list, df


def query_mygene_for_entrezIDs(reporter_query_list):
    """User a query list to query mygene.info for the entrezgene ID and make a
    dictionary that can be used to access the entrezgene ID.
    """
    print("Step 2: START")
    print("Step 2: query mygene.info for entrezgene IDs")
    mg = mygene.MyGeneInfo()
    mg_results = mg.querymany(reporter_query_list, species=species,
                              scopes=reporter_type, fields='entrezgene',
                              verbose=False,
                              entrezonly=True)
    mygene_dict = {}
    for dic in mg_results:
        try:
            mygene_dict[dic['query']] = dic['entrezgene']
        except KeyError:
            pass
    print("Step 2: mygene_dict length: ", len(mygene_dict))
    print("Step 2: END")
    return mygene_dict


def new_list_with_mygene_IDs(reporter_query_list, mygene_dict):
    """Check all the symbols or IDs and find entrezgene/NCBI IDs if they exist.
    If they do not exist, then just keep symbol.

    Returns list in order of input.
    """
    print("Step 3: START")
    print("Step 3: make replacement Entrezgene ID list using mygene dict")

    output_list = []

    replacement_count = 0  # found on mygene
    no_replacement_count = 0  # symbol does not exist on mygene
    fout = open('gene_symbols_without_entrezgeneID.txt', 'w')

    for i in reporter_query_list:
        try:
            output_list.append(mygene_dict[i])  # get entrezgene ID
            replacement_count += 1
        except KeyError:
            # if no entrezgene ID or symbol not on mygene.info
            fout.write(i + '\n')
            # (TODO remove symbol)
            # just keep the symbol, since no Entrezgene symbol is found
            output_list.append(i)
            no_replacement_count += 1

    fout.close()
    print("Step 3: number of symbols replaced with entrezgene IDs: ",
          replacement_count)
    print("Step 3: number of symbols not found on mygene.info: ",
          no_replacement_count)
    print("Step 3: total number of reporter genes: ", len(output_list))
    print("Step 3: END")
    return output_list


def replace_reporter_gene_symbols_with_entrezgene_IDs(df, output_list):
    print("Step 4: START")
    print("Step 4: replace gene symbols with entrezgene IDs")
    df.index = output_list
    df = df.drop(df.columns[0], axis=1)
    print("Step 4: END")
    return df


def main():

    reporter_query_list, df = read_file_get_reporter_query_list(input_seq_file)
    mygene_dict = query_mygene_for_entrezIDs(reporter_query_list)
    output_list = new_list_with_mygene_IDs(reporter_query_list, mygene_dict)
    df = replace_reporter_gene_symbols_with_entrezgene_IDs(df, output_list)
    # write the pandas dataframe to a tab delimited text file
    df.to_csv('rnaseq_dataframe_file.txt', sep='\t')


# (TODO) REMOVE THIS BEFORE SUBMITTING PULL REQUEST
main()
