#! /usr/bin/env python
# -*- coding: utf8 -*-


import re
import sys
from article import ScholarArticle
from utils import ScholarConf

# Import BeautifulSoup -- try 4 first, fall back to older
try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup
    except ImportError:
        print('We need BeautifulSoup, sorry...')
        sys.exit(1)


class ScholarArticleParser(object):

    """
    ScholarArticleParser can parse HTML document strings obtained from
    Google Scholar. This is a base class; concrete implementations
    adapting to tweaks made by Google over time follow below.
    """

    def __init__(self, site=None):
        self.soup = None
        self.article = None
        self.site = site or ScholarConf.SCHOLAR_SITE
        self.year_re = re.compile(r'\b(?:20|19)\d{2}\b')

    def handle_article(self, art):
        """
        The parser invokes this callback on each article parsed
        successfully.  In this base class, the callback does nothing.
        """

    def handle_num_results(self, num_results):
        """
        The parser invokes this callback if it determines the overall
        number of results, as reported on the parsed results page. The
        base class implementation does nothing.
        """

    def parse(self, html):
        """
        This method initiates parsing of HTML content, cleans resulting
        content as needed, and notifies the parser instance of
        resulting instances via the handle_article callback.
        """
        self.soup = BeautifulSoup(html)

        # This parses any global, non-itemized attributes from the page.
        self._parse_globals()

        # Now parse out listed articles:
        for div in self.soup.findAll(ScholarArticleParser._tag_results_checker):
            self._parse_article(div)
            self._clean_article()
            if self.article['title']:
                self.handle_article(self.article)

    def _clean_article(self):
        """
        This gets invoked after we have parsed an article, to do any
        needed cleanup/polishing before we hand off the resulting
        article.
        """
        if self.article['title']:
            self.article['title'] = self.article['title'].strip()

    def _parse_globals(self):
        tag = self.soup.find(name='div', attrs={'id': 'gs_ab_md'})
        if tag is not None:
            raw_text = tag.findAll(text=True)
            # raw text is a list because the body contains <b> etc
            if raw_text is not None and len(raw_text) > 0:
                try:
                    num_results = raw_text[0].split()[1]
                    # num_results may now contain commas to separate
                    # thousands, strip:
                    num_results = num_results.replace(',', '')
                    num_results = int(num_results)
                    self.handle_num_results(num_results)
                except (IndexError, ValueError):
                    pass

    def _parse_article(self, div):
        self.article = ScholarArticle()

        for tag in div:
            if not hasattr(tag, 'name'):
                continue

            if tag.name == 'div' and self._tag_has_class(tag, 'gs_rt') and \
                    tag.h3 and tag.h3.a:
                self.article['title'] = ''.join(tag.h3.a.findAll(text=True))
                self.article['url'] = self._path2url(tag.h3.a['href'])
                if self.article['url'].endswith('.pdf'):
                    self.article['url_pdf'] = self.article['url']

            if tag.name == 'font':
                for tag2 in tag:
                    if not hasattr(tag2, 'name'):
                        continue
                    if tag2.name == 'span' and \
                       self._tag_has_class(tag2, 'gs_fl'):
                        self._parse_links(tag2)

    def _parse_links(self, span):
        for tag in span:
            if not hasattr(tag, 'name'):
                continue
            if tag.name != 'a' or tag.get('href') is None:
                continue

            if tag.get('href').startswith('/scholar?cites'):
                if hasattr(tag, 'string') and tag.string.startswith('Cited by'):
                    self.article['num_citations'] = \
                        self._as_int(tag.string.split()[-1])

                # Weird Google Scholar behavior here: if the original
                # search query came with a number-of-results limit,
                # then this limit gets propagated to the URLs embedded
                # in the results page as well. Same applies to
                # versions URL in next if-block.
                self.article['url_citations'] = \
                    self._strip_url_arg('num', self._path2url(tag.get('href')))

                # We can also extract the cluster ID from the versions
                # URL. Note that we know that the string contains "?",
                # from the above if-statement.
                args = self.article['url_citations'].split('?', 1)[1]
                for arg in args.split('&'):
                    if arg.startswith('cites='):
                        self.article['cluster_id'] = arg[6:]

            if tag.get('href').startswith('/scholar?cluster'):
                if hasattr(tag, 'string') and tag.string.startswith('All '):
                    self.article['num_versions'] = \
                        self._as_int(tag.string.split()[1])
                self.article['url_versions'] = \
                    self._strip_url_arg('num', self._path2url(tag.get('href')))

            if tag.getText().startswith('Import'):
                self.article['url_citation'] = self._path2url(tag.get('href'))

    @staticmethod
    def _tag_has_class(tag, klass):
        """
        This predicate function checks whether a BeatifulSoup Tag instance
        has a class attribute.
        """
        res = tag.get('class') or []
        if type(res) != list:
            # BeautifulSoup 3 can return e.g. 'gs_md_wp gs_ttss',
            # so split -- conveniently produces a list in any case
            res = res.split()
        return klass in res

    @staticmethod
    def _tag_results_checker(tag):
        return tag.name == 'div' \
            and ScholarArticleParser._tag_has_class(tag, 'gs_r')

    @staticmethod
    def _as_int(obj):
        try:
            return int(obj)
        except ValueError:
            return None

    def _path2url(self, path):
        """Helper, returns full URL in case path isn't one."""
        if path.startswith('http://'):
            return path
        if not path.startswith('/'):
            path = '/' + path
        return self.site + path

    def _strip_url_arg(self, arg, url):
        """Helper, removes a URL-encoded argument, if present."""
        parts = url.split('?', 1)
        if len(parts) != 2:
            return url
        res = []
        for part in parts[1].split('&'):
            if not part.startswith(arg + '='):
                res.append(part)
        return parts[0] + '?' + '&'.join(res)


class ScholarArticleParser120726(ScholarArticleParser):

    """
    This class reflects update to the Scholar results page layout that
    Google made 07/26/12.
    """

    def _parse_article(self, div):
        self.article = ScholarArticle()

        for tag in div:
            if not hasattr(tag, 'name'):
                continue
            if str(tag).lower().find('.pdf'):
                if tag.find('div', {'class': 'gs_ttss'}):
                    self._parse_links(tag.find('div', {'class': 'gs_ttss'}))

            if tag.name == 'div' and self._tag_has_class(tag, 'gs_ri'):
                # There are (at least) two formats here. In the first
                # one, we have a link, e.g.:
                #
                # <h3 class="gs_rt">
                #   <a href="http://dl.acm.org/citation.cfm?id=972384" class="yC0">
                #     <b>Honeycomb</b>: creating intrusion detection signatures using
                #        honeypots
                #   </a>
                # </h3>
                #
                # In the other, there's no actual link -- it's what
                # Scholar renders as "CITATION" in the HTML:
                #
                # <h3 class="gs_rt">
                #   <span class="gs_ctu">
                #     <span class="gs_ct1">[CITATION]</span>
                #     <span class="gs_ct2">[C]</span>
                #   </span>
                #   <b>Honeycomb</b> automated ids signature creation using honeypots
                # </h3>
                #
                # We now distinguish the two.
                try:
                    atag = tag.h3.a
                    self.article['title'] = ''.join(atag.findAll(text=True))
                    self.article['url'] = self._path2url(atag['href'])
                    if self.article['url'].endswith('.pdf'):
                        self.article['url_pdf'] = self.article['url']
                except:
                    # Remove a few spans that have unneeded content (e.g.
                    # [CITATION])
                    for span in tag.h3.findAll(name='span'):
                        span.clear()
                    self.article['title'] = ''.join(tag.h3.findAll(text=True))

                if tag.find('div', {'class': 'gs_a'}):
                    year = self.year_re.findall(
                        tag.find('div', {'class': 'gs_a'}).text)
                    self.article['year'] = year[0] if len(year) > 0 else None
                    self.article['authors'] = tag.find('div', {'class': 'gs_a'}).text.split(year[0])[0].strip(', .') if len(year) > 0 else None

                if tag.find('div', {'class': 'gs_fl'}):
                    self._parse_links(tag.find('div', {'class': 'gs_fl'}))

                if tag.find('div', {'class': 'gs_rs'}):
                    # These are the content excerpts rendered into the results.
                    raw_text = tag.find(
                        'div', {'class': 'gs_rs'}).findAll(text=True)
                    if len(raw_text) > 0:
                        raw_text = ''.join(raw_text)
                        raw_text = raw_text.replace('\n', '')
                        self.article['excerpt'] = raw_text
