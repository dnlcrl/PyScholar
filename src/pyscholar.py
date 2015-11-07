#! /usr/bin/env python
# -*- coding: utf8 -*-

import optparse
import sys
import time
import re
from utils import ScholarUtils, ScholarSettings, ScholarConf, output_query, reset_res
from query import ClusterScholarQuery, SearchScholarQuery, ScholarQuerier
import json
import pdb

def loop(options, query, querier, file_name='../res.json'):
    if options.start is not None:
        #options.start = min(options.count, ScholarConf.MAX_PAGE_RESULTS)
        query.set_starting_number(options.start)

    if options.count is not None:
        if options.count > ScholarConf.MAX_PAGE_RESULTS:
            total = options.count
            count = options.count
            start = options.start
            done = 0
            try:
                while done < total:
                    count = min(
                        total-done, ScholarConf.MAX_PAGE_RESULTS)
                    query.set_starting_number(start)
                    query.set_num_page_results(count)
                    querier.send_query(query)
                    time.sleep(1)
                    if len(querier.articles) == 0:
                        break
                    output_query(options, querier, file_name)
                    start += ScholarConf.MAX_PAGE_RESULTS
                    done += count
            except Exception, e:
                print e
                pdb.set_trace()
            finally:
                return 0
        query.set_num_page_results(options.count)

    querier.send_query(query)
    output_query(options, querier, file_name)


def main():
    print ""
    usage = """scholar.py [options] <query string>
A command-line interface to Google Scholar.

Examples:

# Retrieve one article written by Einstein on quantum theory:
scholar.py -c 1 --author "albert einstein" --phrase "quantum theory"

# Retrieve a BibTeX entry for that quantum theory paper:
scholar.py -c 1 -C 17749203648027613321 --citation bt

# Retrieve five articles written by Einstein after 1970 where the title
# does not contain the words "quantum" and "theory":
scholar.py -c 5 -a "albert einstein" -t --none "quantum theory" --after 1970"""

    fmt = optparse.IndentedHelpFormatter(max_help_position=50, width=100)
    parser = optparse.OptionParser(usage=usage, formatter=fmt)
    group = optparse.OptionGroup(parser, 'Query arguments',
                                 'These options define search query arguments and parameters.')
    group.add_option('-a', '--author', metavar='AUTHORS', default=None,
                     help='Author name(s)')
    group.add_option('-A', '--all', metavar='WORDS', default=None, dest='allw',
                     help='Results must contain all of these words')
    group.add_option('-s', '--some', metavar='WORDS', default=None,
                     help='Results must contain at least one of these words. Pass arguments in form -s "foo bar baz" for simple words, and -s "a phrase, another phrase" for phrases')
    group.add_option('-n', '--none', metavar='WORDS', default=None,
                     help='Results must contain none of these words. See -s|--some re. formatting')
    group.add_option('-p', '--phrase', metavar='PHRASE', default=None,
                     help='Results must contain exact phrase')
    group.add_option('-t', '--title-only', action='store_true', default=False,
                     help='Search title only')
    group.add_option('-P', '--pub', metavar='PUBLICATIONS', default=None,
                     help='Results must have appeared in this publication')
    group.add_option('--after', metavar='YEAR', default=None,
                     help='Results must have appeared in or after given year')
    group.add_option('--before', metavar='YEAR', default=None,
                     help='Results must have appeared in or before given year')
    group.add_option('--no-patents', action='store_true', default=False,
                     help='Do not include patents in results')
    group.add_option('--no-citations', action='store_true', default=False,
                     help='Do not include citations in results')
    group.add_option('-C', '--cluster-id', metavar='CLUSTER_ID', default=None,
                     help='Do not search, just use articles in given cluster ID')
    group.add_option('-c', '--count', type='int', default=None,
                     help='Maximum number of results')
    group.add_option('-S', '--start', type='int', default=0,
                     help='Starting page of results')
    group.add_option('-u', '--url', metavar='URL', default=None,
                     help='Citation list\'s url')
    group.add_option('-U', '--urls_file', metavar='URL', dest='urls', default=None,
                     help='Citation list\'s urls json file ([\'http: // scholar.google.com/scholar?cites=4412725301034017472 & as_sdt=2005 & sciodt=1, 5 & hl=en\', ...])')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Output format',
                                 'These options control the appearance of the results.')
    group.add_option('--txt', action='store_true',
                     help='Print article data in text format (default)')
    group.add_option('--txt-globals', action='store_true',
                     help='Like --txt, but first print global results too')
    group.add_option('--csv', action='store_true',
                     help='Print article data in CSV form (separator is "|")')
    group.add_option('--csv-header', action='store_true',
                     help='Like --csv, but print header with column names')
    group.add_option('--json', action='store_true',
                     help='Save article data in JSON form (default file: "../res.json")')
    group.add_option('--citation', metavar='FORMAT', default=None,
                     help='Print article details in standard citation format. Argument Must be one of "bt" (BibTeX), "en" (EndNote), "rm" (RefMan), or "rw" (RefWorks).')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Miscellaneous')
    group.add_option('--cookie-file', metavar='FILE', default=None,
                     help='File to use for cookie storage. If given, will read any existing cookies if found at startup, and save resulting cookies in the end.')
    group.add_option('-d', '--debug', action='count', default=0,
                     help='Enable verbose logging to stderr. Repeated options increase detail of debug output.')
    group.add_option('-v', '--version', action='store_true', default=False,
                     help='Show version information')
    parser.add_option_group(group)

    options, _ = parser.parse_args()

    # Show help if we have neither keyword search nor author name
    if len(sys.argv) == 1:
        parser.print_help()
        return 1

    if options.debug > 0:
        options.debug = min(options.debug, ScholarUtils.LOG_LEVELS['debug'])
        ScholarConf.LOG_LEVEL = options.debug
        ScholarUtils.log('info', 'using log level %d' % ScholarConf.LOG_LEVEL)

    if options.version:
        print('This is scholar.py %s.' % ScholarConf.VERSION)
        return 0

    if options.cookie_file:
        ScholarConf.COOKIE_JAR_FILE = options.cookie_file

    # Sanity-check the options: if they include a cluster ID query, it
    # makes no sense to have search arguments:
    if options.cluster_id is not None:
        if options.author or options.allw or options.some or options.none \
           or options.phrase or options.title_only or options.pub \
           or options.after or options.before:
            print(
                'Cluster ID queries do not allow additional search arguments.')
            return 1

    querier = ScholarQuerier()
    settings = ScholarSettings()

    if options.citation == 'bt':
        settings.set_citation_format(ScholarSettings.CITFORM_BIBTEX)
    elif options.citation == 'en':
        settings.set_citation_format(ScholarSettings.CITFORM_ENDNOTE)
    elif options.citation == 'rm':
        settings.set_citation_format(ScholarSettings.CITFORM_REFMAN)
    elif options.citation == 'rw':
        settings.set_citation_format(ScholarSettings.CITFORM_REFWORKS)
    elif options.citation is not None:
        print(
            'Invalid citation link format, must be one of "bt", "en", "rm", or "rw".')
        return 1

    querier.apply_settings(settings)

    if options.cluster_id:
        query = ClusterScholarQuery(cluster=options.cluster_id)
    else:
        query = SearchScholarQuery()
        if options.author:
            query.set_author(options.author)
        if options.allw:
            query.set_words(options.allw)
        if options.some:
            query.set_words_some(options.some)
        if options.none:
            query.set_words_none(options.none)
        if options.phrase:
            query.set_phrase(options.phrase)
        if options.title_only:
            query.set_scope(True)
        if options.pub:
            query.set_pub(options.pub)
        if options.after or options.before:
            query.set_timeframe(options.after, options.before)
        if options.no_patents:
            query.set_include_patents(False)
        if options.no_citations:
            query.set_include_citations(False)

    if options.url is not None:
        query.set_url(options.url)
        print options.url

    if options.urls is not None:
        print options.urls
        try:
            with open(options.urls) as data_file:
                urls = json.load(data_file)
            if isinstance(urls, list) and len(urls) > 0 and isinstance(urls[0], dict):
                urls = [x['url_citations'] for x in urls]
            for url in urls:
                query.set_url(url)
                reset_res()
                loop(options, query, querier, file_name='../results/' +
                     re.match('.*?([0-9]+)', url).group(1) + '.json')
        except Exception, e:
            print e

    else:
        loop(options, query, querier)
    querier.quit()
    return 0

if __name__ == "__main__":
    sys.exit(main())
