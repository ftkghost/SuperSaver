from datetime import datetime

from django.apps import apps
from django.db.models import manager
from django.db.models import expressions
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


class ProductManager (manager.Manager):
    """
    Custom manager to facilitate product query
    Refs: https://docs.djangoproject.com/en/2.0/topics/db/managers/
    """

    def _get_product_model(self):
        return apps.get_model('product', 'Product')

    def _search_by_keywords_no_sort(self, keywords):
        now = datetime.now().timestamp()
        # Use expressions.Value to represent search_vector column.
        # This can avoid create the search vector for each request.
        # The search_vector has already added as a SearchVectorField and updated by the trigger, we can use it directly.
        products = self.annotate(rank=SearchRank(expressions.Value('search_vector'), keywords)) \
            .filter(active=True,
                    promotion_start_date__lte=now,
                    promotion_end_date__gt=now,
                    search_vector=keywords)
        return products

    def search_by_relevance(self, keywords):
        """
        search product by keyword order by relevance (desc).
        :param keywords: search keyword.
        :return: product query set.
        """
        query_set = self._search_by_keywords_no_sort(keywords)
        return query_set.order_by("-rank")

    def search_by_price(self, keywords):
        """
        search product by keyword order by price (asc).
        :param keywords: search keyword.
        :return: product query set.
        """
        query_set = self._search_by_keywords_no_sort(keywords)
        return query_set.order_by("price")
