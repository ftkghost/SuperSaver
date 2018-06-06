from django.apps import apps
from django.db.models import manager
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


class ProductManager (manager.Manager):
    # Custom manager to facilitate product query
    # Refs: https://docs.djangoproject.com/en/2.0/topics/db/managers/
    def search(self, keywords):
        search_vectors = SearchVector('title', weight='A')  \
                        + SearchVector('description', weight='C')   \
                        + SearchVector('landing_page', weight='D')
        # Avoid import cycle
        Product = apps.get_model('product', 'Product')
        # The search_vector has already added as a SearchVectorField and updated by the trigger, we can use it directly.
        products = Product.objects.annotate(rank=SearchRank(search_vectors, keywords)) \
            .filter(search_vector=keywords).order_by('-rank')
        return products
