from django.contrib import admin
from dataset.models import (BiogpsDataset, BiogpsDatasetData,
                            BiogpsDatasetMatrix, BiogpsDatasetPlatform,
                            BiogpsDatasetFailed)


# Register your models here.
class BiogpsDatasetAdmin(admin.ModelAdmin):
    pass
admin.site.register(BiogpsDataset)


class BiogpsDatasetDataAdmin(admin.ModelAdmin):
    pass
admin.site.register(BiogpsDatasetData)


class BiogpsDatasetMatrixAdmin(admin.ModelAdmin):
    pass
admin.site.register(BiogpsDatasetMatrix)


class BiogpsDatasetPlatformAdmin(admin.ModelAdmin):
    pass
admin.site.register(BiogpsDatasetPlatform)

# 
# class BiogpsDatasetGeoLoadedAdmin(admin.ModelAdmin):
#     pass
# admin.site.register(BiogpsDatasetGeoLoaded)


class BiogpsDatasetFailedAdmin(admin.ModelAdmin):
    pass
admin.site.register(BiogpsDatasetFailed)


