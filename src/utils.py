#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import json
from excepts import FormatError

json_results = []


class ScholarSettings(object):

    """
    This class lets you adjust the Scholar settings for your
    session. It's intended to mirror the features tunable in the
    Scholar Settings pane, but right now it's a bit basic.
    """
    CITFORM_NONE = 0
    CITFORM_REFWORKS = 1
    CITFORM_REFMAN = 2
    CITFORM_ENDNOTE = 3
    CITFORM_BIBTEX = 4

    def __init__(self):
        self.citform = 0  # Citation format, default none
        self.per_page_results = ScholarConf.MAX_PAGE_RESULTS
        self._is_configured = False

    def set_citation_format(self, citform):
        citform = ScholarUtils.ensure_int(citform)
        if citform < 0 or citform > self.CITFORM_BIBTEX:
            raise FormatError('citation format invalid, is "%s"' % citform)
        self.citform = citform
        self._is_configured = True

    def set_per_page_results(self, per_page_results):
        msg = 'page results must be integer'
        self.per_page_results = ScholarUtils.ensure_int(per_page_results, msg)
        self.per_page_results = min(self.per_page_results,
                                    ScholarConf.MAX_PAGE_RESULTS)
        self._is_configured = True

    def is_configured(self):
        return self._is_configured


class ScholarConf(object):

    """Helper class for global settings."""

    VERSION = '2.9'
    LOG_LEVEL = 1
    MAX_PAGE_RESULTS = 10  # Current maximum for per-page results
    STARTING_RESULT = 0  # Result offset (to change page)
    SCHOLAR_SITE = 'http://scholar.google.com'

    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0'

    # If set, we will use this file to read/save cookies to enable
    # cookie use across sessions.
    COOKIE_JAR_FILE = None


class ScholarUtils(object):

    """A wrapper for various utensils that come in handy."""

    LOG_LEVELS = {'error': 1,
                  'warn':  2,
                  'info':  3,
                  'debug': 4}

    @staticmethod
    def ensure_int(arg, msg=None):
        try:
            return int(arg)
        except ValueError:
            raise FormatError(msg)

    @staticmethod
    def log(level, msg):
        if level not in ScholarUtils.LOG_LEVELS.keys():
            return
        if ScholarUtils.LOG_LEVELS[level] > ScholarConf.LOG_LEVEL:
            return
        sys.stderr.write('[%5s]  %s' % (level.upper(), msg + '\n'))
        sys.stderr.flush()


def txt(querier, with_globals):
    if with_globals:
        # If we have any articles, check their attribute labels to get
        # the maximum length -- makes for nicer alignment.
        max_label_len = 0
        if len(querier.articles) > 0:
            items = sorted(list(querier.articles[0].attrs.values()),
                           key=lambda item: item[2])
            max_label_len = max([len(str(item[1])) for item in items])

        # Get items sorted in specified order:
        items = sorted(
            list(querier.query.attrs.values()), key=lambda item: item[2])
        # Find largest label length:
        max_label_len = max([len(str(item[1]))
                             for item in items] + [max_label_len])
        fmt = '[G] %%%ds %%s' % max(0, max_label_len-4)
        for item in items:
            if item[0] is not None:
                print(fmt % (item[1], item[0]))
        if len(items) > 0:
            print

    articles = querier.articles
    for art in articles:
        print(encode(art.as_txt()) + '\n')


def encode(s):
    if isinstance(s, basestring):
        return s.encode('utf-8')  # pylint: disable-msg=C0103
    else:
        return str(s)


def csv(querier, header=False, sep='|'):
    articles = querier.articles
    for art in articles:
        result = art.as_csv(header=header, sep=sep)
        print(encode(result))
        header = False


def reset_res():
    del json_results[:]


def to_json(querier, file_name='../res.json'):
    print 'adding ' + str(len(querier.articles)) + ' articles to json list'
    print 'total articles in json list: ' + str(len(json_results))
    for art in querier.articles:
        json_results.append(
            {key: art.attrs[key][0] for key in art.attrs.keys()})
    with open(file_name, 'wb') as f:
        json.dump(json_results, f)


def citation_export(querier):
    articles = querier.articles
    for art in articles:
        print(art.as_citation() + '\n')


def output_query(options, querier, file_name):
    if options.json:
        to_json(querier, file_name)
    elif options.csv:
        csv(querier)
    elif options.csv_header:
        csv(querier, header=True)
    elif options.citation is not None:
        citation_export(querier)
    else:
        txt(querier, with_globals=options.txt_globals)

    if options.cookie_file:
        querier.save_cookies()
