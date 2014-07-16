from django.conf import settings
from django.views.decorators.http import require_http_methods
import models
from django.http.response import HttpResponse

# Create your views here.
@require_http_methods(["GET"])
def dataset_info(request):
    #try preset ds, then 1
    try:
        ds_id = settings.DEFAULT_DATASET_ID
    except Exception:
        ds_id = 1

    try:
        ds = models.BiogpsDataset.objects.get(id=ds_id)
    except Exception:
        return HttpResponse('{"code":"-1", "detail":"can not found dataset with pk %d"}'%ds_id, content_type="application/json")
    return HttpResponse('{"code":"0", "detail":"can not found dataset with pk %d"}'%ds_id, content_type="application/json")
