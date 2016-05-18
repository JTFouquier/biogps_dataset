Directions for providing RNAseq gene expression data to BioGPS.org:

These directions are intended for a scientist who is submitting data
to BioGPS.org. In essence it is a "readme for the users."

We will need two information files from you, in addition to your sample data.

FILE DETAILS:
=============

1) the "information" sheet:
===========================

Please fill out this sheet and return to your current contact. We will provided
a blank sheet for you to fill out.

Open up in Excel (or similar) and make sure it is saved as a
tab-delimited text file.

*Required fields*: name, summary tags and species.

All other fields should be filled out if possible, but blanks are okay.

Details about fields:

Name: Name or title of the project
Summary: This is a summary paragraph of the project (example:
      http://biogps.org/dataset/E-GEOD-44097/)
Owner: This is your BioGPS ID number if you have one.
Pubmed_id: If your project is published, please provide a PMID (pubmed ID)
geo id numbers: a user may or may not have these values

2) Your metadata file:
======================

This is a tab-delimited text file with headers containing any titles you choose,
and the first column is an index column, common for readability.
*Important*: headers must not contain spaces.

Please note that these are tab-delimited; opening the file in Excel will be
easier, but you should still save as a tab-delimited text file.

The fourth column must contain the sample/condition.

Example:

  data_set_id biological_replicate  condition
1 1.fasta 1 cell treatment 1
2 2.fasta 2 cell treatment 1
3 3.fasta 1 cell treatment 2
4 4.fasta 2 cell treatement 2
