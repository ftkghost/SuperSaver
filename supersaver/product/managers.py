from datetime import datetime

from django.contrib.postgres.search import SearchRank
from django.core.paginator import Paginator
from django.db.models import expressions
from django.db.models import manager


class ProductManager (manager.Manager):
    """
    Custom manager to facilitate product query
    Refs: https://docs.djangoproject.com/en/2.0/topics/db/managers/
    """
    def recent_offers(self, page_num, page_size):
        if page_num <= 0:
            return []
        now = datetime.now().timestamp()
        products = self.filter(active=True, promotion_start_date__lte=now, promotion_end_date__gt=now)  \
            .order_by('promotion_end_date')
        return self._paged_offers(products, page_num, page_size)

    def search_by_relevance(self, keywords, page_num, page_size):
        """
        search product by keyword order by relevance (desc).
        :param keywords: search keyword.
        :return: product query set.
        """
        if page_num <= 0:
            return []
        query_set = self._search_by_keywords_no_sort(keywords)
        return self._paged_offers(query_set.order_by("-rank"), page_num, page_size)

    def search_by_price(self, keywords, page_num, page_size):
        """
        search product by keyword order by price (asc).
        :param keywords: search keyword.
        :return: product query set.
        """
        if page_num <= 0:
            return []
        query_set = self._search_by_keywords_no_sort(keywords)
        return self._paged_offers(query_set.order_by("price"), page_num, page_size)

    @staticmethod
    def _paged_offers(page_queryset, page_num, page_size):
        if page_num <= 0:
            return []
        paged_products = Paginator(page_queryset, page_size)
        if page_num > paged_products.num_pages:
            return []
        page = paged_products.get_page(page_num)
        return page.object_list

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
