import logging
import pandas
from django.conf import settings


class Pattern():
    """
        judge if any element in src martch
        element in target
    """
    def match_any(self, src, target):
        for k in src:
            if k in target:
                return k
        return None


class DP_E_GEOD_4006(Pattern):
    """
        one data file with all sample data in it
        E-MTAB-1169
    """

    sample_keys = ['Scan Name', 'Hybridization Name']
    data_keys = ['Scan REF', 'Hybridization REF']
    platform_keys = ['Array Design REF']
    name = '4006'

    def name(self):
        return self.name

    # check if sdrf and data both match this pattern
    def is_valid(self, sdrf, data, platform):
        # must be single data file
        if len(data.values()) != 1:
            return None

        sample_key = self.match_any(self.sample_keys, sdrf.columns)
        if sample_key is None:
            return None
        platform_key = self.match_any(self.platform_keys, sdrf.columns)
        if platform_key is None:
            return None
        f = list(data.values())[0]
        f.seek(0)
        header = f.readline().strip().split('\t')
        if self.match_any(self.data_keys, header) is None:
            return None
        f.seek(0)
        header[0] = 'REPORTERS'
        df = pandas.read_table(f, names=header, skiprows=2,
                               index_col=['REPORTERS'], delimiter='\t')
        df = df.sort_index(axis=1).sort_index(axis=0)
        sdrf = sdrf.sort(columns=sample_key)
        # filter by platform
        sdrf = sdrf[sdrf[platform_key].isin([platform])]
        if len(sdrf[sample_key]) > 100:
            logging.info('more than 100 samples, ignore')
            return None
        df = df.loc[:, list(sdrf[sample_key])]
        return (sdrf, df)


class DP_E_GEOD_26688(Pattern):
    """
        one data file with one sample data, might contains junk
        E-GEOD-26688
        E-MEXP-3476
    """

    name = '26688'
    sample_keys = ['Derived Array Data File']
    data_keys = ['ID_REF', 'CompositeSequence Identifier']
    platform_keys = ['Array Design REF']

    def name(self):
        return self.name

    def is_valid(self, sdrf, data, platform):
        sample_key = self.match_any(self.sample_keys, sdrf.columns)
        if sample_key is None:
            return None
        f = list(data.values())[0]
        f.seek(0)
        header = f.readline().decode('utf-8').split('\t')
        if self.match_any(self.data_keys, header) is None:
            return None
        platform_key = self.match_any(self.platform_keys, sdrf.columns)
        if platform_key is None:
            return None
        sdrf = sdrf[sdrf[platform_key].isin([platform])]
        if len(sdrf[sample_key]) > settings.MAX_SUPPORTED_SAMPLES:
            logging.info('more than 100 samples, ignore')
            return None
        li = list(sdrf[sample_key])
        df_total = None
        for e in data:
            if e not in li:
                continue
            f = data[e]
            f.seek(0)
            df = pandas.read_table(
                f, names=['REPORTERS', e],
                skiprows=1, usecols=['REPORTERS', e],
                index_col=['REPORTERS'])
            if df_total is None:
                df_total = df
            else:
                df_total = pandas.merge(df_total, df, left_index=True,
                                        right_index=True)
        if df_total is None:
            return None
        df_total = df_total.sort_index(axis=1).sort_index(axis=0)
        sdrf = sdrf.sort(columns=sample_key)
        logging.info('26688 type')
        return (sdrf, df_total)


class ExperimentDataParse:

    def __init__(self, er, platform):
        self.platform = platform
        self.name = er.name
        self.sdrf = er.sdrf
        self.info = er.info
        self.data = er.data_raw
        # self.pattern = None
        self.patterns = [DP_E_GEOD_4006(), DP_E_GEOD_26688()]

    def parse(self):
        # load sdrf into pandas data frames
        self.sdrf.seek(0)
        self.sdrf = pandas.read_table(self.sdrf, header=0)
        # try to load processed data into pandas data frames
        # and record the pattern
        ret = None
        for p in self.patterns:
            ret = p.is_valid(self.sdrf, self.data, self.platform)
            if ret is None:
                continue
            else:
                break
        if ret is None:
            raise Exception('not recognized experiment data')
        self.sdrf, self.data = ret
