from core.model import Site
from sca.settings import SITE_NAME, SITE_DOMAIN


def get_site():
    return Site(SITE_NAME, SITE_DOMAIN)

def get_in_app_url():
    return "nz.co.scamedia://from-web"