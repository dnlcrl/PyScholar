#! /usr/bin/env python
# -*- coding: utf8 -*-


class Error(Exception):

    """Base class for any Scholar error."""


class FormatError(Error):

    """A query argument or setting was formatted incorrectly."""


class QueryArgumentError(Error):

    """A query did not have a suitable set of arguments."""
