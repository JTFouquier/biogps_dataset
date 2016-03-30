
import pandas as pd

import mygene

"""
This is a helper file to return Entrezgene IDs for BioGPS data loading. It is
not necessary to run on all datasets, only those datasets which use a reporter
type that is NOT Entrezgene ID.

The reporter genes provided for local datasets are often the symbol which is
not the correct format for BioGPS.

Entrezgene ID AKA: NCBI gene IDs.

This specific helper file dataset was written for local RNAseq data.

BioGPS typically handles Microarray data and also handles dataloading
from remote data repositories (hosted online) and not local data.
"""

# these 3 variables will be be input as arguments by the user in terminal,
# not in this script
# species = 'mouse'
# input_seq_file = '/Users/fouquier/repos/biogps_dataset/dataset/management/\
# local_data_load/2016.02.10_normalizedcounts_iNswithMEFs.txt'
# output_file = 'rnaseq_data_fixed_reporters.txt'


def read_file_get_reporter_query_list(input_seq_file):
    """Take a users input file from their sequencing run and get a list of the
    reporter genes used. They should all be entrezgene IDs, but most are
    symbols. Attempt to find entrezgene IDs for reporters.
    """
    print("Find Entrezgene IDs for RNA sequencing run reporters\n")
    print("Step 1: START")
    print("Step 1: get reporter gene column as list from RNAseq run data file")

    df = pd.read_table(input_seq_file, sep='\t')
    reporter_query_list = df.ix[:, 0].tolist()
    print("Step 1: END\n")
    return reporter_query_list, df


def query_mygene_for_entrez_ids(reporter_query_list_symbol_search):
    """User a query list to query mygene.info for the entrezgene ID and make a
    dictionary that can be used to access the entrezgene ID.
    """
    print("Step 2: START")
    print("Step 2: query mygene.info for reporter entrezgene IDs")

    # mygene.info Python client:
    mg = mygene.MyGeneInfo()
    mygene_dict = {}

    # reporter search on ***SYMBOL***
    mg_results = mg.querymany(reporter_query_list_symbol_search,
                              species=species,
                              scopes='symbol',
                              fields='entrezgene',
                              verbose=False,
                              entrezonly=True)

    reporter_query_list_alias_search = []
    for dic in mg_results:
        # Entrezgene ID cannot be in the dictionary twice
        # sometimes gene is "not found"; hence try/except
        try:
            if dic['entrezgene'] in mygene_dict.values():
                continue
        except KeyError:
            reporter_query_list_alias_search.append(dic['query'])
            continue
        mygene_dict[dic['query']] = dic['entrezgene']

    # reporter search on ***ALIAS***
    mg_results_second_attempt = mg.querymany(reporter_query_list_alias_search,
                                             species=species,
                                             scopes='alias',
                                             fields='entrezgene',
                                             verbose=False,
                                             entrezonly=True)

    print("STEP 2: number of failed reporter to entrezgene ID searches "
          "(symbol search): ", len(reporter_query_list_alias_search))

    total_reporters_without_entrezgene_ID = []

    for dic in mg_results_second_attempt:
        # Entrezgene ID cannot be in the dictionary twice
        # sometimes gene is "not found"; hence try/except
        try:
            if dic['entrezgene'] in mygene_dict.values():
                continue
        except KeyError:
            total_reporters_without_entrezgene_ID.append(dic['query'])
            continue
        mygene_dict[dic['query']] = dic['entrezgene']

    print("STEP 2: from failed 'reporter to entrezgene ID search based "
          "on symbol', search remaining reporters using alias")
    print("STEP 2: number of failed reporter to entrezgene ID searches "
          "(alias search): ", len(total_reporters_without_entrezgene_ID))
    print("Step 2: mygene_dict length: ", len(mygene_dict))
    print("Step 2: END\n")
    return mygene_dict


def new_list_with_mygene_ids(reporter_query_list, mygene_dict):
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
            # just keep the symbol or alias, since no Entrezgene symbol is found
            # This isn't really necessary because symbol or alias cannot be
            # used to visualize data on BioGPS, but it's a placeholder.
            output_list.append(i)
            no_replacement_count += 1
    fout.close()

    print("Step 3: Total number of symbols/aliases replaced with "
          "entrezgene IDs: ", replacement_count)
    print("Step 3: Total number of symbols or aliases not found "
          "on mygene.info: ", no_replacement_count)
    print("Step 3: total number of reporter genes: ", len(output_list))
    print("Step 3: END\n")
    return output_list


def replace_reporter_gene_symbols_with_entrezgene_ids(df, output_list):
    print("Step 4: START")
    print("Step 4: replace gene symbols with entrezgene IDs")
    df.index = output_list
    df = df.drop(df.columns[0], axis=1)
    print("Step 4: END\n")
    return df


def main(input_seq_file, output_file, species):
    reporter_query_list, df = read_file_get_reporter_query_list(input_seq_file)
    mygene_dict = query_mygene_for_entrez_ids(reporter_query_list)
    output_list = new_list_with_mygene_ids(reporter_query_list, mygene_dict)
    df = replace_reporter_gene_symbols_with_entrezgene_ids(df, output_list)
    # (TODO) *** Not sure the proper location of inputs and output files.
    # write the pandas dataframe to a tab delimited text file
    df.to_csv(output_file, sep='\t')


# main(input_seq_file, output_file, species)
