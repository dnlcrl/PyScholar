# PyScholar
A "supervised" parser for Google Scholar, written in Python.

PyScholar is a command line tool written in python that implements a querier and parser for Google Scholar's output. This project is inspired by scholar.py, in fact there is a lot of code from that project, the main difference is that scholar.py makes use of the urllib modules, thus, so no javascript, and given that people at big G don't like you to scrape their search results, when the server responses the "I'm not a robot" page, you simply get no output from scholar.py, for a long time. Instead PyScholar makes use of selenium webdriver giving the ability to see what's going on and in case the "I'm not a robot" shows up you can simply pass the challenge manually and let the scraper continue his job.

Also there are some other new features I inclulded from my scholar.py fork, that are: json exporting of the reults, "starting result" option, and the potential ability to get an unlimited number results, even if it seems that results are limited on server-side to approximately one thousand.

I also removed Python 3 support, sorry.

**I include here the original [scholar.py](https://github.com/ckreibich/scholar.py)'s README.md content, changelog and license (change "scholar.py" with "pyscholar.py" in the commands below in order to make it work):**

scholar.py is a Python module that implements a querier and parser for Google Scholar's output. Its classes can be used independently, but it can also be invoked as a command-line tool.

The script used to live at http://icir.org/christian/scholar.html, and I've moved it here so I can more easily manage the various patches and suggestions I'm receiving for scholar.py. Thanks guys, for all your interest! If you'd like to get in touch, email me at christian@icir.org or ping me [on Twitter](http://twitter.com/ckreibich).

Cheers,<br>
Christian

Features
--------

* Extracts publication title, most relevant web link, PDF link, number of citations, number of online versions, link to Google Scholar's article cluster for the work, Google Scholar's cluster of all works referencing the publication, and excerpt of content.
* Extracts total number of hits as reported by Scholar (new in version 2.5)
* Supports the full range of advanced query options provided by Google Scholar, such as title-only search, publication date timeframes, and inclusion/exclusion of patents and citations.
* Supports article cluster IDs, i.e., information relating to the variants of an article already identified by Google Scholar
* Supports retrieval of citation details in standard external formats as provided by Google Scholar, including BibTeX and EndNote.
* Command-line tool prints entries in CSV format, simple plain text, or in the citation export format.
* Cookie support for higher query volume, including ability to persist cookies to disk across invocations.

Note
----

I will always strive to add features that increase the power of this
API, but I will never add features that intentionally try to work
around the query limits imposed by Google Scholar. Please don't ask me
to add such features.

Examples
--------

Try scholar.py --help for all available options. Note, the command line arguments changed considerably in version 2.0! A few examples:

Retrieve one article written by Einstein on quantum theory:

    $ scholar.py -c 1 --author "albert einstein" --phrase "quantum theory"
             Title On the quantum theory of radiation
               URL http://icole.mut-es.ac.ir/downloads/Sci_Sec/W1/Einstein%201917.pdf
              Year 1917
         Citations 184
          Versions 3
        Cluster ID 17749203648027613321
          PDF link http://icole.mut-es.ac.ir/downloads/Sci_Sec/W1/Einstein%201917.pdf
    Citations list http://scholar.google.com/scholar?cites=17749203648027613321&as_sdt=2005&sciodt=0,5&hl=en
     Versions list http://scholar.google.com/scholar?cluster=17749203648027613321&hl=en&as_sdt=0,5
           Excerpt The formal similarity between the chromatic distribution curve for thermal radiation [...]


Note the cluster ID in the above. Using this ID, you can directly access the cluster of articles Google Scholar has already determined to be variants of the same paper. So, let's see the versions:

    $ scholar.py -C 17749203648027613321
             Title On the quantum theory of radiation
               URL http://icole.mut-es.ac.ir/downloads/Sci_Sec/W1/Einstein%201917.pdf
         Citations 184
          Versions 0
        Cluster ID 17749203648027613321
          PDF link http://icole.mut-es.ac.ir/downloads/Sci_Sec/W1/Einstein%201917.pdf
    Citations list http://scholar.google.com/scholar?cites=17749203648027613321&as_sdt=2005&sciodt=0,5&hl=en
           Excerpt The formal similarity between the chromatic distribution curve for thermal radiation [...]

             Title ON THE QUANTUM THEORY OF RADIATION
               URL http://www.informationphilosopher.com/solutions/scientists/einstein/1917_Radiation.pdf
         Citations 0
          Versions 0
          PDF link http://www.informationphilosopher.com/solutions/scientists/einstein/1917_Radiation.pdf
           Excerpt The formal similarity between the chromatic distribution curve for thermal radiation [...]
    
             Title The Quantum Theory of Radiation
               URL http://web.ihep.su/dbserv/compas/src/einstein17/eng.pdf
         Citations 0
          Versions 0
          PDF link http://web.ihep.su/dbserv/compas/src/einstein17/eng.pdf
           Excerpt 1 on the assumption that there are discrete elements of energy, from which quantum [...]


Let's retrieve a BibTeX entry for that quantum theory paper. The best BibTeX often seems to be the one linked from search results, not those in the article cluster, so let's do a search again:

    $ scholar.py -c 1 --author "albert einstein" --phrase "quantum theory" --citation bt
    @article{einstein1917quantum,
      title={On the quantum theory of radiation},
      author={Einstein, Albert},
      journal={Phys. Z},
      volume={18},
      pages={121--128},
      year={1917}
    }

Report the total number of articles Google Scholar has for Einstein:

    $ scholar.py --txt-globals --author "albert einstein" | grep '\[G\]' | grep Results
    [G]    Results 4190


ChangeLog
---------
* 2.9   Fixed Unicode problem in certain queries. Thanks to smidm for
      this contribution.
* 2.8   Improved quotation-mark handling for multi-word phrases in
      queries. Also, log URLs %-decoded in debugging output, for
      easier interpretation.
* 2.7   Ability to extract content excerpts as reported in search results.
      Also a fix to -s|--some and -n|--none: these did not yet support
      passing lists of phrases. This now works correctly if you provide
      separate phrases via commas.
* 2.6   Ability to disable inclusion of patents and citations. This
      has the same effect as unchecking the two patents/citations
      checkboxes in the Scholar UI, which are checked by default.
      Accordingly, the command-line options are --no-patents and
      --no-citations.
* 2.5:  Ability to parse global result attributes. This right now means
      only the total number of results as reported by Scholar at the
      top of the results pages (e.g. "About 31 results"). Such
      global result attributes end up in the new attrs member of the
      used ScholarQuery class. To render those attributes, you need
      to use the new --txt-globals flag.
      Rendering global results is currently not supported for CSV
      (as they don't fit the one-line-per-article pattern). For
      grepping, you can separate the global results from the
      per-article ones by looking for a line prefix of "[G]":
      $ scholar.py --txt-globals -a "Einstein"
      [G]    Results 11900
               Title Can quantum-mechanical description of physical reality be considered complete?
                 URL http://journals.aps.org/pr/abstract/10.1103/PhysRev.47.777
                Year 1935
           Citations 12804
            Versions 80
             Cluster ID 8174092782678430881
      Citations list http://scholar.google.com/scholar?cites=8174092782678430881&as_sdt=2005&sciodt=0,5&hl=en
       Versions list http://scholar.google.com/scholar?cluster=8174092782678430881&hl=en&as_sdt=0,5
* 2.4:  Bugfixes:
      - Correctly handle Unicode characters when reporting results
        in text format.
      - Correctly parse citation-only (i.e. linkless) results in
        Google Scholar results.
* 2.3:  Additional features:
      - Direct extraction of first PDF version of an article
      - Ability to pull up an article cluster's results directly.
      This is based on work from @aliparsai on GitHub -- thanks!
      - Suppress missing search results (so far shown as "None" in
        the textual output form.
* 2.2:  Added a logging option that reports full HTML contents, for
      debugging, as well as incrementally more detailed logging via
      -d up to -dddd.
* 2.1:  Additional features:
      - Improved cookie support: the new --cookie-file options
        allows the reuse of a cookie across invocations of the tool;
        this allows higher query rates than would otherwise result
        when invoking scholar.py repeatedly.
      - Workaround: remove the num= URL-encoded argument from parsed
        URLs. For some reason, Google Scholar decides to propagate
        the value from the original query into the URLs embedded in
        the results.
* 2.0:  Thorough overhaul of design, with substantial improvements:
      - Full support for advanced search arguments provided by
        Google Scholar
      - Support for retrieval of external citation formats, such as
        BibTeX or EndNote
      - Simple logging framework to track activity during execution
* 1.7:  Python 3 and BeautifulSoup 4 compatibility, as well as printing
      of usage info when no options are given. Thanks to Pablo
      Oliveira (https://github.com/pablooliveira)!
      Also a bunch of pylinting and code cleanups.
* 1.6:  Cookie support, from Matej Smid (https://github.com/palmstrom).
* 1.5:  A few changes:
      - Tweak suggested by Tobias Isenberg: use unicode during CSV
        formatting.
      - The option -c|--count now understands numbers up to 100 as
        well. Likewise suggested by Tobias.
      - By default, text rendering mode is now active. This avoids
        confusion when playing with the script, as it used to report
        nothing when the user didn't select an explicit output mode.
* 1.4:  Updates to reflect changes in Scholar's page rendering,
      contributed by Amanda Hay at Tufts -- thanks!
* 1.3:  Updates to reflect changes in Scholar's page rendering.
* 1.2:  Minor tweaks, mostly thanks to helpful feedback from Dan Bolser.
      Thanks Dan!
* 1.1:  Made author field explicit, added --author option.


License
-------

scholar.py is using the standard [BSD license](http://opensource.org/licenses/BSD-2-Clause).
