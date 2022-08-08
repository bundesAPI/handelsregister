#!/usr/bin/env python3

import logging
import mechanize
import re
import pathlib
import sys
from bs4 import BeautifulSoup

logger = logging.getLogger("mechanize")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class HandelsRegister:
    def __init__(self):
        self.browser = mechanize.Browser()

        self.browser.set_debug_http(True)
        self.browser.set_debug_responses(True)
        # browser.set_debug_redirects(True)

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
            ("Accept-Language", "en-GB,en;q=0.9"),
            ("Accept-Encoding", "gzip, deflate, br"),
            (
                "Accept",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            ),
            ("Connection", "keep-alive"),
        ]
        self.cachedir = pathlib.Path('cache')
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def open_startpage(self):
        self.browser.open("https://www.handelsregister.de", timeout=10)

    def companyname2cachename(self, companyname):
        # map a companyname to a filename, that caches the downloaded HTML, so re-running this script touches the
        # webserver less often.
        return self.cachedir / companyname

    def search_company(self, exact_name, force=False):
        # force = True skips the cache.
        cachename = self.companyname2cachename(exact_name)
        if force==False and cachename.exists():
            with open(cachename, 'r') as f:
                html = f.read()
                print('return cached content for %s' % exact_name)
        else:

            # TODO implement token bucket to abide by rate limit
            # Use an atomic counter: https://gist.github.com/benhoyt/8c8a8d62debe8e5aa5340373f9c509c7
            response_search = self.browser.follow_link(text="Advanced search")

            print(self.browser.title())

            self.browser.select_form(name="form")

            self.browser["form:schlagwoerter"] = exact_name
            self.browser["form:schlagwortOptionen"] = ["3"] # 3 -> contain the exact name of the company.

            response_result = self.browser.submit()

            print(self.browser.title())

            html = response_result.read().decode("utf-8")
            with open(self.cachedir / exact_name, 'w') as f:
                f.write(html)

            # TODO catch the situation if there's more than one company?
            # TODO get all documents attached to the exact company
            # TODO parse useful information out of the PDFs

        return html


def parse_result(result):
    cells = []
    for cellnum, cell in enumerate(result.find_all('td')):
        #print('[%d]: %s [%s]' % (cellnum, cell.text, cell))
        cells.append(cell.text)
    assert cells[7] == 'History'
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

def get_companies_in_searchresults(fn):
    with open(fn, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
        grid = soup.find('table', role='grid')
        #print('grid: %s', grid)
      
        results = []
        for result in grid.find_all('tr'):
            if a := result.get('data-ri'):
                index = int(a)
                #print('r[%d] %s' % (index, result))
                d = parse_result(result)
                results.append(d)
    return results

if __name__ == "__main__":
    companyname = 'Gasag AG'
    #companyname = '1&1 Mail & Media Development & Technology GmbH'
    h = HandelsRegister()
    h.open_startpage()
    h.search_company(companyname)
    companies = get_companies_in_searchresults(h.companyname2cachename(companyname))
    for c in companies:
        pr_company_info(c)
