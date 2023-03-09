from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

from urllib.parse import urlencode

ALL_SITES_URL = 'http://www.craigslist.org/about/sites'
SITE_URL = 'http://%s.craigslist.org'
USER_AGENT = 'Mozilla/5.0'

install = GeckoDriverManager().install()
driver = webdriver.Firefox(service=FirefoxService(install))


def bs(content):
    return BeautifulSoup(content, 'html.parser')


def isiterable(var):
    try:
        return iter(var) and True
    except TypeError:
        return False


def requests_get(*args, **kwargs):
    """
    Retries if a RequestException is raised (could be a connection error or
    a timeout).
    """
    logger = kwargs.pop('logger', None)
    # Set default User-Agent header if not defined.
    # kwargs.setdefault('headers', {}).setdefault('User-Agent', USER_AGENT)
    print(kwargs)
    if kwargs:
        query_string = urlencode(kwargs["params"])
        print(query_string)
        url = args[0] +  "?" + query_string
    else:
        url = args[0]
    try:
        driver.get(url)
        return driver
    except RequestException as exc:
        if logger:
            logger.warning('Request failed (%s). Retrying ...', exc)
        driver.get(url)
        return driver


def get_all_sites():
    response = requests.get(ALL_SITES_URL)
    response.raise_for_status()  # Something failed?
    soup = BeautifulSoup(response.content, 'html.parser')
    sites = set()

    for box in soup.findAll('div', {'class': 'box'}):
        for a in box.findAll('a'):
            # Remove protocol and get subdomain
            site = a.attrs['href'].rsplit('//', 1)[1].split('.')[0]
            sites.add(site)

    return sites


def get_all_areas(site):
    response = requests.get(SITE_URL % site)
    response.raise_for_status()  # Something failed?
    soup = BeautifulSoup(response.content, 'html.parser')
    raw = soup.select('ul.sublinks li a')
    sites = set(a.attrs['href'].rsplit('/')[1] for a in raw)
    return sites


def get_list_filters(url):
    list_filters = {}
    response = requests_get(url)
    print(response.page_source)
    soup = bs(response.page_source)
    for list_filter in soup.find_all('div', class_='search-attribute'):
        filter_key = list_filter.attrs['data-attr']
        filter_labels = list_filter.find_all('label')
        options = {opt.text.strip(): opt.find('input').get('value')
                   for opt in filter_labels}
        list_filters[filter_key] = {'url_key': filter_key, 'value': options}
    return list_filters
