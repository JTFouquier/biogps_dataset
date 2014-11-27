from django.contrib import admin
from dataset.models import (BiogpsDataset,
                            BiogpsDatasetPlatform, BiogpsDatasetFailed)


class BiogpsDatasetAdmin(admin.ModelAdmin):
    list_display = ('geo_gse_id', 'platform',)
    list_filter = ('platform',)
    search_fields = ['geo_gse_id']

admin.site.register(BiogpsDataset, BiogpsDatasetAdmin)


# class BiogpsDatasetDataAdmin(admin.ModelAdmin):
#     pass
# admin.site.register(BiogpsDatasetData)


# class BiogpsDatasetMatrixAdmin(admin.ModelAdmin):
#     exclude = ('_matrix', )
# admin.site.register(BiogpsDatasetMatrix)


class BiogpsDatasetPlatformAdmin(admin.ModelAdmin):
    list_display = ('platform', 'dataset',)

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


