import logging
import mechanize
import sys

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

        self.browser.open("https://www.handelsregister.de", timeout=10)

    def search_company(self, exact_name):
        response_search = self.browser.follow_link(text="Advanced search")

        print(self.browser.title())

        self.browser.select_form(name="form")

        self.browser["form:schlagwoerter"] = exact_name
        self.browser["form:schlagwortOptionen"] = ["3"]

        response_result = self.browser.submit()

        print(self.browser.title())

        html = response_result.read().decode("utf-8")
        open("output.html", "w").write(html)

        # TODO catch the situation if there's more than one company?
        # TODO get all documents attached to the exact company
        # TODO parse useful information out of the PDFs

        return html


if __name__ == "__main__":
    h = HandelsRegister()

    h.search_company("Gasag AG")
