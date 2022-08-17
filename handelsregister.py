#!/usr/bin/env python3
"""
bundesAPI/handelsregister is the command-line interface for for the shared register of companies portal for the German federal states.
You can query, download, automate and much more, without using a web browser.
"""

import argparse
import mechanize
import re
import pathlib
import sys
from bs4 import BeautifulSoup

# Dictionaries to map arguments to values
schlagwortOptionen = {
    "all": 1,
    "min": 2,
    "exact": 3
}

class HandelsRegister:
    def __init__(self, args):
        self.args = args
        self.browser = mechanize.Browser()

        self.browser.set_debug_http(args.debug)
        self.browser.set_debug_responses(args.debug)
        # self.browser.set_debug_redirects(True)

        self.browser.set_handle_robots(False)
        self.browser.set_handle_equiv(True)
        self.browser.set_handle_gzip(True)
        self.browser.set_handle_refresh(False)
        self.browser.set_handle_redirect(True)
        self.browser.set_handle_referer(True)

        self.browser.addheaders = [
            (
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
            ),
            (   "Accept-Language", "en-GB,en;q=0.9"   ),
            (   "Accept-Encoding", "gzip, deflate, br"    ),
            (
                "Accept",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            ),
            (   "Connection", "keep-alive"    ),
        ]
        
        self.cachedir = pathlib.Path("cache")
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def open_startpage(self):
        self.browser.open("https://www.handelsregister.de", timeout=10)

    def companyname2cachename(self, companyname):
        # map a companyname to a filename, that caches the downloaded HTML, so re-running this script touches the
        # webserver less often.
        return self.cachedir / companyname

    def search_company(self):
        cachename = self.companyname2cachename(self.args.schlagwoerter)
        if self.args.force==False and cachename.exists():
            with open(cachename, "r") as f:
                html = f.read()
                print("return cached content for %s" % self.args.schlagwoerter)
        else:
            # TODO implement token bucket to abide by rate limit
            # Use an atomic counter: https://gist.github.com/benhoyt/8c8a8d62debe8e5aa5340373f9c509c7
            response_search = self.browser.follow_link(text="Advanced search")

            if self.args.debug == True:
                print(self.browser.title())

            self.browser.select_form(name="form")

            self.browser["form:schlagwoerter"] = args.schlagwoerter
            so_id = schlagwortOptionen.get(args.schlagwortOptionen)

            self.browser["form:schlagwortOptionen"] = [str(so_id)]

            response_result = self.browser.submit()

            if self.args.debug == True:
                print(self.browser.title())

            html = response_result.read().decode("utf-8")
            with open(cachename, "w") as f:
                f.write(html)

            # TODO catch the situation if there's more than one company?
            # TODO get all documents attached to the exact company
            # TODO parse useful information out of the PDFs
        return get_companies_in_searchresults(html)


def parse_result(result):
    cells = []
    for cellnum, cell in enumerate(result.find_all('td')):
        #print('[%d]: %s [%s]' % (cellnum, cell.text, cell))
        cells.append(cell.text.strip())
    #assert cells[7] == 'History'
    d = {}
    d['court'] = cells[1]
    d['name'] = cells[2]
    d['state'] = cells[3]
    d['status'] = cells[4]
    d['documents'] = cells[5] # todo: get the document links
    d['history'] = []
    hist_start = 8
    hist_cnt = (len(cells)-hist_start)/3
    for i in range(hist_start, len(cells), 3):
        d['history'].append((cells[i], cells[i+1])) # (name, location)
    #print('d:',d)
    return d

def pr_company_info(c):
    for tag in ('name', 'court', 'state', 'status'):
        print('%s: %s' % (tag, c.get(tag, '-')))
    print('history:')
    for name, loc in c.get('history'):
        print(name, loc)

def get_companies_in_searchresults(html):
    soup = BeautifulSoup(html, 'html.parser')
    grid = soup.find('table', role='grid')
    #print('grid: %s', grid)
  
    results = []
    for result in grid.find_all('tr'):
        a = result.get('data-ri')
        if a is not None:
            index = int(a)
            #print('r[%d] %s' % (index, result))
            d = parse_result(result)
            results.append(d)
    return results

def parse_args():
# Parse arguments
    parser = argparse.ArgumentParser(description='A handelsregister CLI')
    parser.add_argument(
                          "-d",
                          "--debug",
                          help="Enable debug mode and activate logging",
                          action="store_true"
                        )
    parser.add_argument(
                          "-f",
                          "--force",
                          help="Force a fresh pull and skip the cache",
                          action="store_true"
                        )
    parser.add_argument(
                          "-s",
                          "--schlagwoerter",
                          help="Search for the provided keywords",
                          required=True,
                          default="Gasag AG" # TODO replace default with a generic search term
                        )
    parser.add_argument(
                          "-so",
                          "--schlagwortOptionen",
                          help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
                          choices=["all", "min", "exact"],
                          default="all"
                        )
    args = parser.parse_args()


    # Enable debugging if wanted
    if args.debug == True:
        import logging
        logger = logging.getLogger("mechanize")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.DEBUG)

    return args

if __name__ == "__main__":
    args = parse_args()
    h = HandelsRegister(args)
    h.open_startpage()
    companies = h.search_company()
    if companies is not None:
        for c in companies:
            pr_company_info(c)
