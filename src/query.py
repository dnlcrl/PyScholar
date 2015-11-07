#! /usr/bin/env python
# -*- coding: utf8 -*-
"""
This module provides classes for querying Google Scholar and parsing
returned results. It currently *only* processes the first results
page. It is not a recursive crawler.
"""
import time
from utils import ScholarConf, ScholarUtils, encode
from parser import ScholarArticleParser120726
from excepts import QueryArgumentError
from urllib import quote, unquote
import pdb
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import FirefoxProfile
from os import path
from shutil import copytree, rmtree

FF_PROFILE_PATH = '../ffprofile'

class ScholarQuery(object):

    """
    The base class for any kind of results query we send to Scholar.
    """

    def __init__(self):
        self.url = None

        # The number of results requested from Scholar -- not the
        # total number of results it reports (the latter gets stored
        # in attrs, see below).
        self.num_results = ScholarConf.MAX_PAGE_RESULTS

        #
        #
        #
        self.starting_number = ScholarConf.STARTING_RESULT

        # Queries may have global result attributes, similar to
        # per-article attributes in ScholarArticle. The exact set of
        # attributes may differ by query type, but they all share the
        # basic data structure:
        self.attrs = {}

    def set_starting_number(self, starting_number):
        msg = 'starting number of results on page must be numeric'
        self.starting_number = ScholarUtils.ensure_int(starting_number, msg)

    def set_num_page_results(self, num_page_results):
        msg = 'maximum number of results on page must be numeric'
        self.num_results = ScholarUtils.ensure_int(num_page_results, msg)

    def get_url(self):
        """
        Returns a complete, submittable URL string for this particular
        query instance. The URL and its arguments will vary depending
        on the query.
        """
        return None

    def _add_attribute_type(self, key, label, default_value=None):
        """
        Adds a new type of attribute to the list of attributes
        understood by this query. Meant to be used by the constructors
        in derived classes.
        """
        if len(self.attrs) == 0:
            self.attrs[key] = [default_value, label, 0]
            return
        idx = max([item[2] for item in self.attrs.values()]) + 1
        self.attrs[key] = [default_value, label, idx]

    def __getitem__(self, key):
        """Getter for attribute value. Returns None if no such key."""
        if key in self.attrs:
            return self.attrs[key][0]
        return None

    def __setitem__(self, key, item):
        """Setter for attribute value. Does nothing if no such key."""
        if key in self.attrs:
            self.attrs[key][0] = item

    def _parenthesize_phrases(self, query):
        """
        Turns a query string containing comma-separated phrases into a
        space-separated list of tokens, quoted if containing
        whitespace. For example, input

          'some words, foo, bar'

        becomes

          '"some words" foo bar'

        This comes in handy during the composition of certain queries.
        """
        if query.find(',') < 0:
            return query
        phrases = []
        for phrase in query.split(','):
            phrase = phrase.strip()
            if phrase.find(' ') > 0:
                phrase = '"' + phrase + '"'
            phrases.append(phrase)
        return ' '.join(phrases)


class ClusterScholarQuery(ScholarQuery):

    """
    This version just pulls up an article cluster whose ID we already
    know about.
    """
    args = 'start=%(num)s' \
        + '&cluster=%(cluster)s' \
        + '&num=%(num)s'
    SCHOLAR_CLUSTER_URL = ScholarConf.SCHOLAR_SITE + '/scholar?' + args

    def __init__(self, cluster=None):
        ScholarQuery.__init__(self)
        self._add_attribute_type('num_results', 'Results', 0)
        self.cluster = None
        self.set_cluster(cluster)

    def set_cluster(self, cluster):
        """
        Sets search to a Google Scholar results cluster ID.
        """
        msg = 'cluster ID must be numeric'
        self.cluster = ScholarUtils.ensure_int(cluster, msg)

    def set_url(self, url):
        self.SCHOLAR_CLUSTER_URL = url + '&' + self.args

    def get_url(self):
        if self.cluster is None:
            raise QueryArgumentError('cluster query needs cluster ID')

        urlargs = {'cluster': self.cluster,
                   'num': self.num_results or ScholarConf.MAX_PAGE_RESULTS}

        for key, val in urlargs.items():
            urlargs[key] = quote(encode(val))

        return self.SCHOLAR_CLUSTER_URL % urlargs


class SearchScholarQuery(ScholarQuery):

    """
    This version represents the search query parameters the user can
    configure on the Scholar website, in the advanced search options.
    """
    args = 'start=%(start)s' \
        + '&as_q=%(words)s' \
        + '&as_epq=%(phrase)s' \
        + '&as_oq=%(words_some)s' \
        + '&as_eq=%(words_none)s' \
        + '&as_occt=%(scope)s' \
        + '&as_sauthors=%(authors)s' \
        + '&as_publication=%(pub)s' \
        + '&as_ylo=%(ylo)s' \
        + '&as_yhi=%(yhi)s' \
        + '&as_sdt=%(patents)s%%2C5' \
        + '&as_vis=%(citations)s' \
        + '&btnG=&hl=en' \
        + '&num=%(num)s'
    SCHOLAR_QUERY_URL = ScholarConf.SCHOLAR_SITE + '/scholar?' + args

    def __init__(self):
        ScholarQuery.__init__(self)
        self._add_attribute_type('starting_number', 'Start', 0)
        self._add_attribute_type('num_results', 'Results', 0)
        self.words = None  # The default search behavior
        self.words_some = None  # At least one of those words
        self.words_none = None  # None of these words
        self.phrase = None
        self.scope_title = False  # If True, search in title only
        self.author = None
        self.pub = None
        self.timeframe = [None, None]
        self.include_patents = True
        self.include_citations = True
        self.url = None

    def set_words(self, words):
        """Sets words that *all* must be found in the result."""
        self.words = words

    def set_words_some(self, words):
        """Sets words of which *at least one* must be found in result."""
        self.words_some = words

    def set_words_none(self, words):
        """Sets words of which *none* must be found in the result."""
        self.words_none = words

    def set_phrase(self, phrase):
        """Sets phrase that must be found in the result exactly."""
        self.phrase = phrase

    def set_scope(self, title_only):
        """
        Sets Boolean indicating whether to search entire article or title
        only.
        """
        self.scope_title = title_only

    def set_author(self, author):
        """Sets names that must be on the result's author list."""
        self.author = author

    def set_pub(self, pub):
        """Sets the publication in which the result must be found."""
        self.pub = pub

    def set_timeframe(self, start=None, end=None):
        """
        Sets timeframe (in years as integer) in which result must have
        appeared. It's fine to specify just start or end, or both.
        """
        if start:
            start = ScholarUtils.ensure_int(start)
        if end:
            end = ScholarUtils.ensure_int(end)
        self.timeframe = [start, end]

    def set_include_citations(self, yesorno):
        self.include_citations = yesorno

    def set_include_patents(self, yesorno):
        self.include_patents = yesorno

    def set_url(self, url):
        self.url = url
        if not url.startswith(ScholarConf.SCHOLAR_SITE):
            raise QueryArgumentError('The provided url is not valid')
        self.SCHOLAR_QUERY_URL = url + '&' + self.args

    def get_url(self):
        if self.words is None and self.words_some is None \
           and self.words_none is None and self.phrase is None \
           and self.author is None and self.pub is None \
           and self.timeframe[0] is None and self.timeframe[1] is None \
           and self.url is None:
            raise QueryArgumentError('search query needs more parameters')

        # If we have some-words or none-words lists, we need to
        # process them so GS understands them. For simple
        # space-separeted word lists, there's nothing to do. For lists
        # of phrases we have to ensure quotations around the phrases,
        # separating them by whitespace.
        words_some = None
        words_none = None

        if self.words_some:
            words_some = self._parenthesize_phrases(self.words_some)
        if self.words_none:
            words_none = self._parenthesize_phrases(self.words_none)

        urlargs = {'start': self.starting_number or ScholarConf.STARTING_RESULT,
                   'words': self.words or '',
                   'words_some': words_some or '',
                   'words_none': words_none or '',
                   'phrase': self.phrase or '',
                   'scope': 'title' if self.scope_title else 'any',
                   'authors': self.author or '',
                   'pub': self.pub or '',
                   'ylo': self.timeframe[0] or '',
                   'yhi': self.timeframe[1] or '',
                   'patents': '0' if self.include_patents else '1',
                   'citations': '0' if self.include_citations else '1',
                   'num': self.num_results or ScholarConf.MAX_PAGE_RESULTS}

        for key, val in urlargs.items():
            urlargs[key] = quote(encode(val))

        return self.SCHOLAR_QUERY_URL % urlargs


class ScholarQuerier(object):

    """
    ScholarQuerier instances can conduct a search on Google Scholar
    with subsequent parsing of the resulting HTML content.  The
    articles found are collected in the articles member, a list of
    ScholarArticle instances.
    """

    # Default URLs for visiting and submitting Settings pane, as of 3/14
    GET_SETTINGS_URL = ScholarConf.SCHOLAR_SITE + '/scholar_settings?' \
        + 'sciifh=1&hl=en&as_sdt=0,5'

    SET_SETTINGS_URL = ScholarConf.SCHOLAR_SITE + '/scholar_setprefs?' \
        + 'start=%(start)s' \
        + 'q=' \
        + '&scisig=%(scisig)s' \
        + '&inststart=0' \
        + '&as_sdt=1,5' \
        + '&as_sdtp=' \
        + '&num=%(num)s' \
        + '&scis=%(scis)s' \
        + '%(scisf)s' \
        + '&hl=en&lang=all&instq=&inst=569367360547434339&save='

    # Older URLs:
    # ScholarConf.SCHOLAR_SITE +
    # '/scholar?q=%s&hl=en&btnG=Search&as_sdt=2001&as_sdtp=on

    class Parser(ScholarArticleParser120726):

        def __init__(self, querier):
            ScholarArticleParser120726.__init__(self)
            self.querier = querier

        def handle_num_results(self, num_results):
            if self.querier is not None and self.querier.query is not None:
                self.querier.query['num_results'] = num_results

        def handle_article(self, art):
            self.querier.add_article(art)

    def __init__(self):
        self.articles = []
        self.query = None
        try:
            profile = FirefoxProfile(FF_PROFILE_PATH)
            self.firefox = webdriver.Firefox(profile)

        except Exception, e:

            self.firefox = webdriver.Firefox()

        self.settings = None  # Last settings object, if any

    def apply_settings(self, settings):
        """
        Applies settings as provided by a ScholarSettings instance.
        """
        if settings is None or not settings.is_configured():
            return True

        self.settings = settings

        # This is a bit of work. We need to actually retrieve the
        # contents of the Settings pane HTML in order to extract
        # hidden fields before we can compose the query for updating
        # the settings.

        self.firefox.get(self.GET_SETTINGS_URL)

        tag = self.firefox.find_element_by_id('gs_settings_form')
        #tag = soup.find(name='form', attrs={'id': 'gs_settings_form'})
        if tag is None:
            ScholarUtils.log('info', 'parsing settings failed: no form')
            return False

        tag = [x for x in self.firefox.find_elements_by_tag_name('input') if x.get_attribute(
            'type') == 'hidden' and x.get_attribute('name') == 'scisig'][0]
        if tag is None:
            ScholarUtils.log('info', 'parsing settings failed: scisig')
        #     return False

        urlargs = {'start': settings.starting_number,
                   'scisig': tag['value'],
                   'num': settings.per_page_results,
                   'scis': 'no',
                   'scisf': ''}

        if settings.citform != 0:
            urlargs['scis'] = 'yes'
            urlargs['scisf'] = '&scisf=%d' % settings.citform

        self.firefox.get(self.SET_SETTINGS_URL % urlargs)

        ScholarUtils.log('info', 'settings applied')
        return True

    def send_query(self, query):
        """
        This method initiates a search query (a ScholarQuery instance)
        with subsequent parsing of the response.
        """
        self.clear_articles()
        self.query = query

        html = self._get_http_response(url=query.get_url(),
                                       log_msg='dump of query response HTML',
                                       err_msg='results retrieval failed')
        if html is None:
            return
        self.parse(html)

    def get_citation_data(self, article):
        """
        Given an article, retrieves citation link. Note, this requires that
        you adjusted the settings to tell Google Scholar to actually
        provide this information, *prior* to retrieving the article.
        """
        if article['url_citation'] is None:
            return False
        if article.citation_data is not None:
            return True

        ScholarUtils.log('info', 'retrieving citation export data')
        data = self._get_http_response(url=article['url_citation'],
                                       log_msg='citation data response',
                                       err_msg='requesting citation data failed')
        if data is None:
            return False

        article.set_citation_data(data)
        return True

    def parse(self, html):
        """
        This method allows parsing of provided HTML content.
        """
        parser = self.Parser(self)
        parser.parse(html)

    def add_article(self, art):
        self.get_citation_data(art)
        self.articles.append(art)

    def clear_articles(self):
        """Clears any existing articles stored from previous queries."""
        self.articles = []

    def _get_http_response(self, url, log_msg=None, err_msg=None):
        """
        Helper method, sends HTTP request and returns response payload.
        """
        if log_msg is None:
            log_msg = 'HTTP response data follow'
        if err_msg is None:
            err_msg = 'request failed'
        try:
            ScholarUtils.log('info', 'requesting %s' % unquote(url))

            text = 'Please show you\'re not a robot'
            text2 = 'Per continuare, digita i caratteri nell\'immagine sottostante:'
            while True:
                self.firefox.get(url)
                time.sleep(1)
                html = self.firefox.page_source.encode('utf-8')
                if text in html or text2 in html:
                    pdb.set_trace()
                    html = self.firefox.page_source.encode('utf-8')
                break

            ScholarUtils.log('debug', log_msg)
            ScholarUtils.log('debug', '>>>>' + '-'*68)
            ScholarUtils.log('debug', 'data:\n' + html.decode('utf-8'))
            ScholarUtils.log('debug', '<<<<' + '-'*68)

            return html
        except Exception as err:
            print err
            pdb.set_trace()
            return None

    def quit(self):
        if path.exists(FF_PROFILE_PATH):
            rmtree(FF_PROFILE_PATH)
        copytree(self.firefox.profile.path, FF_PROFILE_PATH)
        self.firefox.quit()
