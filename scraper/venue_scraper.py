import re, math, time, requests
from bs4 import BeautifulSoup

def crawl_core_min(source="CORE2023", search="", timeout=20, delay=0.2):
    # search = "" -> get all
    base = "https://portal.core.edu.au/conf-ranks/"
    sess = requests.Session()
    sess.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    items, page, total_pages = [], 1, None
    while True:
        params = {"by":"all","source":source,"sort":"arank","search":search,"page":page}
        r = sess.get(base, params=params, timeout=timeout); r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        if total_pages is None:
            info = soup.find(string=re.compile(r"Showing\s+results", re.I))
            if info:
                m = re.search(r"of\s+(\d+)", info)
                if m: total_pages = math.ceil(int(m.group(1))/50)
        table = soup.find("table")
        if not table: break
        page_rows = 0
        for tr in table.find_all("tr"):
            if tr.find("th"): continue
            tds = tr.find_all("td")
            if len(tds) < 4: continue
            title = " ".join(tds[0].get_text(" ", strip=True).split())
            acronym = tds[1].get_text(" ", strip=True).upper()
            rank = tds[3].get_text(" ", strip=True).upper().replace(" ","")
            if title or acronym or rank:
                items.append({"title": title, "acronym": acronym, "rank": rank})
                page_rows += 1
        if page_rows == 0: break
        page += 1
        if total_pages and page > total_pages: break
        time.sleep(delay)
    return items

print(crawl_core_min())