"""Minimal browser-like client for driving a local Gibbon install in tests."""
import re
import html
import urllib.parse
import urllib.request
import http.cookiejar
from html.parser import HTMLParser

import os
BASE = os.environ.get("GIBBON_URL", "http://127.0.0.1:8088")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class FormParser(HTMLParser):
    """Collects every <form> with its action and input/select/textarea defaults."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms, self.cur, self.select, self.textarea = [], None, None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self.cur = {"action": html.unescape(a.get("action") or ""), "id": a.get("id", ""), "fields": {}, "radios": {}, "selects": {}}
            self.forms.append(self.cur)
        if self.cur is None:
            return
        name = a.get("name")
        if tag == "input" and name:
            t = (a.get("type") or "text").lower()
            if t in ("submit", "button", "file"):
                return
            if t in ("radio", "checkbox"):
                self.cur["radios"].setdefault(name, []).append(a.get("value"))
                if "checked" in a:
                    self.cur["fields"][name] = a.get("value")
            else:
                self.cur["fields"].setdefault(name, a.get("value") or "")
        elif tag == "select" and name:
            self.select = name
            self.cur["selects"][name] = []
            self.select_chosen = False
            self.cur["fields"].setdefault(name, "")
        elif tag == "option" and self.select:
            v = a.get("value", "")
            self.cur["selects"][self.select].append(v)
            if "selected" in a:
                self.cur["fields"][self.select] = v
                self.select_chosen = True
        elif tag == "textarea" and name:
            self.textarea = name
            self.cur["fields"].setdefault(name, "")

    def handle_endtag(self, tag):
        if tag == "select":
            # Like a browser: with no option marked selected, the first option is the value
            if self.select and self.cur is not None and not getattr(self, "select_chosen", True) and self.cur["selects"].get(self.select):
                self.cur["fields"][self.select] = self.cur["selects"][self.select][0]
            self.select = None
        if tag == "textarea":
            self.textarea = None
        if tag == "form":
            self.cur = None

    def handle_data(self, data):
        if self.textarea and self.cur is not None:
            self.cur["fields"][self.textarea] += data


class Client:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    def request(self, url, data=None, follow=True):
        if not url.startswith("http"):
            url = BASE + "/" + url.lstrip("/")
        body = None
        if data is not None:
            body = urllib.parse.urlencode(data, doseq=True).encode()
        for _ in range(10):
            req = urllib.request.Request(url.replace(" ", "%20"), data=body)
            try:
                resp = self.opener.open(req)
                return url, resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303) and follow:
                    loc = e.headers.get("Location")
                    url = urllib.parse.urljoin(url, loc)
                    body = None
                    continue
                if e.code in (301, 302, 303):
                    return e.headers.get("Location"), ""
                raise
        raise RuntimeError("too many redirects")

    @staticmethod
    def forms(page):
        p = FormParser()
        p.feed(page)
        return p.forms

    def login(self, username, password):
        _, page = self.request("index.php")
        f = [f for f in self.forms(page) if "login" in f["action"]][0]
        fields = dict(f["fields"], username=username, password=password)
        url, page = self.request(f["action"], fields)
        assert "Logout" in page or "logout" in page, "login failed"
        return page


def alerts(page):
    """Visible Gibbon alert messages on a page, flattened to text."""
    out = []
    for m in re.finditer(r"<div[^>]*class=['\"][^'\"]*(?:error|warning|success|message)[^'\"]*['\"][^>]*>(.*?)</div>", page, re.S):
        t = re.sub(r"<[^>]+>", "", m.group(1))
        t = re.sub(r"\s+", " ", html.unescape(t)).strip()
        if t:
            out.append(t)
    return out
