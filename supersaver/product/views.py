from django.shortcuts import render
from .models import Product
from .settings import OFFERS_PER_PAGE
from core.result import ApiResult
from django.http import HttpResponse
# Create your views here.


CONTENT_TYPE_JSON = "application/json"


def get_deals(request):
    response = ApiResult(Product.objects.recent_offers(1, OFFERS_PER_PAGE))
    return HttpResponse(response.to_json(), content_type=CONTENT_TYPE_JSON)


def search_deals(request):
    keywords = 'grey'
    response = ApiResult(Product.objects.search_by_price(keywords, 1, OFFERS_PER_PAGE))
    return HttpResponse(response.to_json(), content_type=CONTENT_TYPE_JSON)

