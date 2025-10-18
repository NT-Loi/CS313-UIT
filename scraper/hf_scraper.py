from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
import requests

logger = logging.getLogger("hf_crawler")
logging.basicConfig(
    filename='arxiv.log',             
    encoding='utf-8',
    level=logging.DEBUG,                 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HuggingFaceScraper:
    def __init__(self):
        self.base_url = "https://huggingface.co/papers/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        url = f"{self.base_url}{paper_id}"
        response = requests.get(url, headers=self.headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch paper {paper_id}. Status code: {response.status_code}")
            return {'arxiv_id': paper_id,
                    'github_stars': None,
                    'upvote': 0,
                    'citing_models': 0,
                    'citing_datasets': 0, 
                    'citing_spaces': 0, 
                    'citing_collections': 0
                }
        
        soup = BeautifulSoup(response.text, 'html.parser')

        github_stars = self._get_github_stars(soup)
        upvote = self._get_upvote(soup)
        res = {'arxiv_id': paper_id,
                'github_stars': github_stars,
                'upvote': upvote}
        
        span_attributes = ['citing_models', 'citing_datasets', 'citing_spaces', 'citing_collections']
        span_tags = soup.find_all("span", {'class': 'ml-3 font-normal text-gray-400'})
        for (span_tag, span_attribute) in zip(span_tags, span_attributes):
            res[span_attribute] = int(span_tag.text)

        return res

    def _get_github_stars(self, soup: BeautifulSoup) -> int:
        github_tag = soup.find("a", {'class': 'btn inline-flex h-9 items-center'}, href=lambda href: href and "github.com" in href)
        if github_tag:
            # Find the star count inside that tag (look for <span> containing number)
            star_span = github_tag.find("span")
            star_count = star_span.get_text(strip=True) if star_span else None

            # Normalize star_count
            if 'k' in star_count:
                star_count = star_count.replace('k', '')
                star_count = float(star_count) * 1000
            elif 'm' in star_count:
                star_count = star_count.replace('m', '')
                star_count = float(star_count) * 1000000
            return int(star_count)
        else:
            return None
        
    def _get_upvote(self, soup: BeautifulSoup) -> int:
        upvote_div = soup.find("div", class_="font-semibold text-orange-500")
        upvote_count = upvote_div.get_text(strip=True) if upvote_div else None
        if upvote_count == '-':
            return 0
        else:
            return int(upvote_count)
        
if __name__ == '__main__':
    hf_scraper = HuggingFaceScraper()
    print(hf_scraper.get_paper_details('2410.15022'))        