from django.contrib import admin
from dataset.models import (BiogpsDataset,
                            BiogpsDatasetPlatform, BiogpsDatasetFailed)


class BiogpsDatasetAdmin(admin.ModelAdmin):
    list_display = ('id', 'geo_gse_id', 'platform',  'sample_count',
                    'factor_count', '_factors', 'is_default')
    list_filter = ('platform',)
    list_display_links = ('geo_gse_id',)
    search_fields = ['geo_gse_id']

    def factor_count(self, obj):
        smps = obj.metadata['factors']
        factor_keys = []
        for smp in smps:
            fv = smp.values()[0]['factorvalue']
            for f in fv:
                if f not in factor_keys:
                    factor_keys.append(f)
        return len(factor_keys)
    factor_count.short_description = 'no. of factors'

    def _factors(self, obj):
        if len(obj.factors) == 0:
            return None
        return ' | '.join(obj.factors[0].keys())
    _factors.short_description = 'factors'
admin.site.register(BiogpsDataset, BiogpsDatasetAdmin)


# class BiogpsDatasetDataAdmin(admin.ModelAdmin):
#     pass
# admin.site.register(BiogpsDatasetData)


# class BiogpsDatasetMatrixAdmin(admin.ModelAdmin):
#     exclude = ('_matrix', )
# admin.site.register(BiogpsDatasetMatrix)


class BiogpsDatasetPlatformAdmin(admin.ModelAdmin):
    list_display = ('platform', 'dataset', 'name', 'spcecies')
    exclude = ('reporters',)

    def dataset(self, obj):
        return obj.dataset_platform.count()

admin.site.register(BiogpsDatasetPlatform, BiogpsDatasetPlatformAdmin)

#
# class BiogpsDatasetGeoLoadedAdmin(admin.ModelAdmin):
#     pass
# admin.site.register(BiogpsDatasetGeoLoaded)


class BiogpsDatasetFailedAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'platform', 'reason',)
    list_filter = ('platform',)
    search_fields = ['dataset']

admin.site.register(BiogpsDatasetFailed, BiogpsDatasetFailedAdmin)


