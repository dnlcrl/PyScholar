#! /usr/bin/env python
# -*- coding: utf8 -*-


class ScholarArticle(object):

    """
    A class representing articles listed on Google Scholar.  The class
    provides basic dictionary-like behavior.
    """

    def __init__(self):
        # The triplets for each keyword correspond to (1) the actual
        # value, (2) a user-suitable label for the item, and (3) an
        # ordering index:
        self.attrs = {
            'title':         [None, 'Title',          0],
            'url':           [None, 'URL',            1],
            'year':          [None, 'Year',           2],
            'num_citations': [0,    'Citations',      3],
            'num_versions':  [0,    'Versions',       4],
            'cluster_id':    [None, 'Cluster ID',     5],
            'url_pdf':       [None, 'PDF link',       6],
            'url_citations': [None, 'Citations list', 7],
            'url_versions':  [None, 'Versions list',  8],
            'url_citation':  [None, 'Citation link',  9],
            'excerpt':       [None, 'Excerpt',       10],
        }

        # The citation data in one of the standard export formats,
        # e.g. BibTeX.
        self.citation_data = None

    def __getitem__(self, key):
        if key in self.attrs:
            return self.attrs[key][0]
        return None

    def __len__(self):
        return len(self.attrs)

    def __setitem__(self, key, item):
        if key in self.attrs:
            self.attrs[key][0] = item
        else:
            self.attrs[key] = [item, key, len(self.attrs)]

    def __delitem__(self, key):
        if key in self.attrs:
            del self.attrs[key]

    def set_citation_data(self, citation_data):
        self.citation_data = citation_data

    def as_txt(self):
        # Get items sorted in specified order:
        items = sorted(list(self.attrs.values()), key=lambda item: item[2])
        # Find largest label length:
        max_label_len = max([len(str(item[1])) for item in items])
        fmt = '%%%ds %%s' % max_label_len
        res = []
        for item in items:
            if item[0] is not None:
                res.append(fmt % (item[1], item[0]))
        return '\n'.join(res)

    def as_csv(self, header=False, sep='|'):
        # Get keys sorted in specified order:
        keys = [pair[0] for pair in
                sorted([(key, val[2]) for key, val in list(self.attrs.items())],
                       key=lambda pair: pair[1])]
        res = []
        if header:
            res.append(sep.join(keys))
        res.append(sep.join([unicode(self.attrs[key][0]) for key in keys]))
        return '\n'.join(res)

    def as_citation(self):
        """
        Reports the article in a standard citation format. This works only
        if you have configured the querier to retrieve a particular
        citation export format. (See ScholarSettings.)
        """
        return self.citation_data or ''
