'''
Models for datasets loaded from ArrayExpress
'''
import base64
import types
import textwrap
from django.db import models
# from django.utils.encoding import smart_unicode
from django.template.defaultfilters import slugify
from django_extensions.db.fields import AutoSlugField
# https://github.com/bradjasper/django-jsonfield
from jsonfield import JSONField


def wrap_str(_str, max_len):
    """ Textwrap _str to provided max length """
    len_str = len(_str)
    if len_str > max_len and len_str > 3:
        _str = textwrap.wrap(_str, max_len - 3)[0] + '...'
    return _str


class BiogpsDatasetManager(models.Manager):
    """Retrieve dataset via GEO or dataset ID"""
    def get(self, *args, **kwargs):
        if 'id' in kwargs and \
           type(kwargs['id']) in types.StringTypes and \
           kwargs['id'][:3].upper() in ['GDS', 'GSE']:

            _id = kwargs['id']
            _id_prefix = _id[:3].upper()
            try:
                if _id_prefix == 'GDS':
                    return super(BiogpsDatasetManager, self).get(
                        geo_gds_id=_id)
                elif _id_prefix == 'GSE':
                    return super(BiogpsDatasetManager, self).get(
                        geo_gse_id=_id)
            except (AttributeError, BiogpsDataset.DoesNotExist):
                raise BiogpsDataset.DoesNotExist
        else:
            # Non-id kwargs passed; business as usual
            try:
                return super(BiogpsDatasetManager, self).get(*args, **kwargs)
            except (AttributeError, BiogpsDataset.DoesNotExist, TypeError,
                    ValueError):
                # Invalid dataset ID
                raise BiogpsDataset.DoesNotExist


class BiogpsDataset(models.Model):
    """Model definition for BiogpsDataset"""
    name = models.CharField(max_length=500)
    summary = models.CharField(blank=True, max_length=10000)
    # ownerprofile = models.ForeignKey(UserProfile, to_field='sid')
    ownerprofile_id = models.CharField(max_length=100)
    platform = models.ForeignKey('BiogpsDatasetPlatform',
                                 related_name='dataset_platform', null=True)
    geo_gds_id = models.CharField(max_length=100)
    geo_gse_id = models.CharField(max_length=100)
    geo_id_plat = models.CharField(max_length=100)
    metadata = JSONField(blank=False, editable=True)
    lastmodified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    slug = AutoSlugField(max_length=50, populate_from='name')
    species = models.CharField(max_length=200)

#     @property
#     def factors_text(self):
#         def format_factor(factor):
#             """ Remove commas, split on spaces for indexing """
#             uf = smart_unicode(factor)
#             formatted = set()
#             facs = uf.replace(',', '').split(' ')
#             for f in facs:
#                 formatted.add(f)
#             return formatted
#
#         _fac_txt = set()
#         for fac_dict in self.metadata['factors']:
#             for sample in fac_dict.values():
#                 for key, val in sample.iteritems():
#                     for k in format_factor(key):
#                         _fac_txt.add(k)
#                     for v in format_factor(val):
#                         _fac_txt.add(v)
#         return ' '.join(_fac_txt)
    # serialize object data for es index setup
    def es_index_serialize(self):
        return {"name": self.name,\
                "summary": self.summary, "geo_gse_id": str(self.geo_gse_id)}

    @property
    def name_wrapped(self):
        return wrap_str(self.name, 140)

    @property
    def name_wrapped_short(self):
        return wrap_str(self.name, 60)

    @property
    def sample_count(self):
        return len(self.metadata['factors'])

    @property
    def sample_ids(self):
        _samples = []
        for f in self.metadata['factors']:
            _samples.append(f.keys()[0])
        return _samples

    @property
    def summary_wrapped(self):
        return wrap_str(self.summary, 140)

    # Custom manager
    # objects = BiogpsDatasetManager()

    # Required setting for ModelWithPermission and PermissionManager working
    object_type = 'D'

    # Short_name will be used as the index_type for ES indexing
    short_name = 'dataset'

    class Meta:
        permissions = (
            ("can_share_dataset", "Can share dataset with others."),
        )
        ordering = ("name",)
        get_latest_by = 'lastmodified'

#     def __unicode__(self):
#         return u('"%s" by "%s"' % (self.name, self.ownerprofile_id))

    @models.permalink
    def get_absolute_url(self):
        """ Return the appropriate URL for this dataset. """
        _slug = slugify(self.name)
        if _slug:
            return ('dataset_show', [str(self.id), _slug])
        else:
            return ('dataset_show', [str(self.id), ])

    def object_cvt(self, mode='ajax'):
        """A helper function to convert a BiogpsDataset object to a simplified
            python dictionary, with all values in python's primary types only.
            Such a dictionary can be passed directly to fulltext indexer or
            serializer for ajax return.

          @param mode: can be one of ['ajax', 'es'], used to return slightly
                                        different dictionary for each purpose.
          @return: an python dictionary
        """
        ds = self
        if mode == 'ajax':
            extra_attrs = {
                'AS_IS': ['geo_gse_id', 'name', 'name_wrapped', 'species']
            }
            out = self._object_cvt(extra_attrs=extra_attrs, mode=mode)
            out.update({
                'default': ds.metadata['default'],
                'display_params': ds.metadata['display_params'],
                'factors': ds.metadata['factors'],
                'geo_gpl_id': ds.metadata['geo_gpl_id'],
                'owner': ds.metadata['owner'],
                'pubmed_id': ds.metadata['pubmed_id'],
                'summary': ds.metadata['summary']
            })
        elif mode == 'es':
            extra_attrs = {'AS_IS': [
                           'factors_text', 'geo_gds_id',
                           'geo_gse_id', 'name', 'name_wrapped',
                           'name_wrapped_short', 'platform_id',
                           'popularity', 'sample_count', 'sample_ids',
                           'slug', 'species', 'summary',
                           'summary_wrapped']}
            out = self._object_cvt(extra_attrs=extra_attrs, mode=mode)
            out.update({
                'default': ds.metadata['default'],
                'display_params': ds.metadata['display_params'],
                'factors': ds.metadata['factors'],
                'geo_gpl_id': ds.metadata['geo_gpl_id'],
                'pubmed_id': ds.metadata['pubmed_id']
            })
        else:
            raise ValueError('Unknown "mode" value.')
        return out


class BiogpsDatasetData(models.Model):
    """Model definition for BiogpsDatasetData"""
    dataset = models.ForeignKey(BiogpsDataset, related_name='dataset_data')
    reporter = models.CharField(max_length=200)
    data = JSONField(blank=False, editable=True)

    class Meta:
        unique_together = ("dataset", "reporter")


class BiogpsDatasetMatrix(models.Model):
    """Model definition for BiogpsDatasetMatrix"""
    dataset = models.OneToOneField(BiogpsDataset,
                                   related_name='dataset_matrix')
    reporters = JSONField(blank=False, editable=True)
    _matrix = models.TextField(db_column='matrix')

    def get_data(self):
        return base64.decodestring(self._matrix)

    def set_data(self, matrix):
        self._matrix = base64.encodestring(matrix)

    matrix = property(get_data, set_data)


class BiogpsDatasetPlatform(models.Model):
    """Model definition for BiogpsDatasetPlatform"""
    platform = models.CharField(max_length=100)
    reporters = JSONField(blank=False, editable=True)


class BiogpsDatasetGeoLoaded(models.Model):
    """Model definition for BiogpsDatasetGeoLoaded. This model tracks what
       GEO datasets have been loaded."""
    geo_type = models.CharField(max_length=20)
    dataset = models.OneToOneField(BiogpsDataset, \
                                   related_name='dataset_geo_loaded')
    with_platform = models.CharField(max_length=100)


class BiogpsDatasetGeoFlagged(models.Model):
    """Model definition for BiogpsDatasetGeoFlagged. This model tracks what
       GEO datasets have been flagged, and the reason why."""
    geo_type = models.CharField(max_length=10)
    dataset = models.OneToOneField(BiogpsDataset, \
                                   related_name='dataset_geo_flagged')
    reason = models.CharField(max_length=1000)


class BiogpsDatasetProcessing(models.Model):
    """Model definition for BiogpsDatasetProcessing. This model tracks what
       datasets are currently being loaded, to allow for multi-threaded
       processing."""
    datasets = JSONField(blank=False, editable=True)


class BiogpsDatasetFailed(models.Model):
    """Model definition for BiogpsDatasetFailed. This model records datasets that
        failed to load.
    """
    platform = models.CharField(max_length=20, null=True)
    dataset = models.CharField(max_length=20, null=True)
    reason = models.TextField(null=True)
