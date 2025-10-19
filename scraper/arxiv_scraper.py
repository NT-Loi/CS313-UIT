import requests
from bs4 import BeautifulSoup, NavigableString
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re
import io
from PyPDF2 import PdfReader

logger = logging.getLogger("arxiv_crawler")
logging.basicConfig(
    filename='arxiv.log',             
    encoding='utf-8',
    level=logging.DEBUG,                 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ArxivScraper:
    def __init__(self):
        self.base_url = "https://arxiv.org/abs/"
        self.search_url = "https://arxiv.org/search/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """
        Fetch paper details from arXiv using the paper ID.
        
        Args:
            paper_id (str): The arXiv paper ID (e.g., '2301.00001')
            
        Returns:
            dict: Paper details including title, authors, abstract, etc.
                 Returns None if the paper cannot be found or an error occurs.
        """
        # try:
        url = f"{self.base_url}{paper_id}"
        response = requests.get(url, headers=self.headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch paper {paper_id}. Status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # DEBUG
        # with open('test.html', 'w') as file:
        #     file.write(soup.prettify())
        
        # Extract paper details
        title = self._get_title(soup)
        authors = self._get_authors(soup)
        abstract = self._get_abstract(soup)
        categories = self._get_categories(soup)
        submission_info = self._get_submission_info(soup)
        keywords = self._get_paper_keywords(paper_id)
        num_pages_paper = self._get_paper_num_pages(paper_id)
        
        logger.info(f"Successfully fetched paper {paper_id}: {title}")
        
        return {
            "arxiv_id": paper_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published_date": submission_info.get("published_date"),
            "last_revised_date": submission_info.get("last_revised_date"),
            "num_revisions": submission_info.get("num_revisions"),
            "pdf_url": f"https://arxiv.org/pdf/{paper_id}.pdf",
            "primary_category": categories.get('primary_category'),
            "categories": categories.get('categories'),
            "keywords": keywords,
            "num_pages": num_pages_paper
        }
            
        # except Exception as e:
        #     logger.error(f"Error fetching paper {paper_id}: {str(e)}")
        #     return None

    def _get_title(self, soup: BeautifulSoup) -> str:
        """Extract paper title from the soup object."""
        title_element = soup.find('h1', {'class': 'title mathjax'})
        if title_element:
            return title_element.text.replace('Title:', '').strip()
        return ''

    def _get_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract authors list from the soup object."""
        authors_div = soup.find('div', {'class': 'authors'})
        if authors_div:
            return [author.text.strip() for author in authors_div.find_all('a')]
        return []

    def _get_abstract(self, soup: BeautifulSoup) -> str:
        """Extract abstract from the soup object."""
        abstract_element = soup.find('blockquote', {'class': 'abstract mathjax'})
        if abstract_element:
            return abstract_element.text.replace('Abstract:', '').strip()
        return ''

    def _get_categories(self, soup):
        """Extract categories from the soup object."""
        # Look for the subjects span to get primary_category
        categories = {
            'primary_category': None,
            'categories': []
        }

        subjects_span = soup.find('span', {'class': 'primary-subject'})
        if subjects_span:
            categories['primary_category'] = subjects_span.text.strip()
            
            # There is no secondary-subject class
            # # Also get secondary subjects if available
            # secondary = soup.find_all('span', {'class': 'secondary-subject'})
            # for sec in secondary:
            #     categories.append(sec.text.strip())
            
            # return categories
        
        # Look in the tablecell to get all categories
        tablecell = soup.find('td', {'class': 'tablecell subjects'})
        if tablecell:
            text = tablecell.text.strip()
            # Remove labels and split by semicolons
            text = text.replace('Subjects:', '').strip()
            categories['categories'] = [cat.strip() for cat in text.split(';') if cat.strip()]
        
        return categories

    def _get_submission_info(self, soup: BeautifulSoup) -> Dict[str, Optional[datetime]]:
        """Extract submission history from the soup object."""
        raw_text = soup.find('div', {'class': 'dateline'}).text
        submission_info = {
        'published_date': None,
        'last_revised_date': None,
        'num_revisions': 0
        }

        # Regex patterns
        submitted_pattern = re.search(r'Submitted on (\d{1,2} [A-Za-z]+ \d{4})(?: \(v(\d+)\))?', raw_text)
        revised_pattern = re.search(r'last revised (\d{1,2} [A-Za-z]+ \d{4}).*v(\d+)\)', raw_text)

        date_format = "%d %b %Y"  # e.g., "1 Jul 2025"
        
        # --- Published date ---
        if submitted_pattern:
            try:
                published_date = datetime.strptime(submitted_pattern.group(1), date_format)
            except ValueError:
                published_date = None
            submission_info['published_date'] = published_date
        else:
            published_date = None
        first_version = 1

        # --- Revised date (optional) ---
        if revised_pattern:
            try:
                last_revised_date = datetime.strptime(revised_pattern.group(1), date_format)
            except ValueError:
                last_revised_date = published_date
            last_version = int(revised_pattern.group(2))
        else:
            # No revision info -> same as published date
            last_revised_date = published_date
            last_version = first_version

        submission_info['last_revised_date'] = last_revised_date
        submission_info['num_revisions'] = max(0, last_version - first_version)

        return submission_info

    def _get_paper_keywords(self, paper_id: str):
        url = f"https://arxiv.org/html/{paper_id}"
        try:
            res = requests.get(url)
            res.raise_for_status()
        except Exception:
            return None  # Không in lỗi ra màn hình

        soup = BeautifulSoup(res.text, "html.parser")

        # Tìm phần chứa chữ "keywords:" (không phân biệt hoa/thường)
        for tag in soup.find_all(string=lambda t: t and "keywords:" in t.lower()):
            parent = tag.parent
            if parent:
                # Trường hợp text nằm trong cùng thẻ
                full_text = parent.get_text(" ", strip=True)
                if "keywords:" in full_text.lower():
                    parts = full_text.lower().split("keywords:")
                    if len(parts) > 1:
                        keywords_raw = parts[-1]
                        keywords = [kw.strip(' ".,;') for kw in keywords_raw.split(",") if kw.strip()]
                        if keywords:
                            return keywords

                # Trường hợp text nằm kế bên trong DOM
                next_texts = []
                for sibling in parent.next_siblings:
                    if isinstance(sibling, NavigableString):
                        next_texts.append(sibling.strip())
                    elif sibling.name not in ["button", "br"]:
                        next_texts.append(sibling.get_text(" ", strip=True))
                joined = " ".join(next_texts).strip()
                if joined:
                    keywords = [kw.strip(' ".,;') for kw in joined.split(",") if kw.strip()]
                    if keywords:
                        return keywords

        return None  # Nếu không tìm thấy gì

    def _get_paper_num_pages(self, paper_id: str) -> int:
        """
        Trích xuất số trang của paper từ file PDF arXiv.
        Args:
            paper_id (str): Mã arXiv, ví dụ '2510.14539v1'
        Returns:
            int: Số trang (hoặc None nếu không lấy được)
        """
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        try:
            response = requests.get(pdf_url, timeout=20)
            response.raise_for_status()
            with io.BytesIO(response.content) as pdf_file:
                reader = PdfReader(pdf_file)
                return len(reader.pages)
        except Exception as e:
            return None

    def search_by_category_year(self, category: str, year:int = 2020, max_results: int = 10) -> List[Dict]:
        """
        Search for paper_ids in a specific category.
        
        Args:
            category (str): arXiv category (e.g., 'cs.AI')
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of paper_ids found
        """
        
        paper_ids = []
        start = 0
        
        logger.info(f"Starting search for category {category}, max_results={max_results}")
        
        while len(paper_ids) < max_results:
            # Fixed URL format - the size parameter should be the page size, not start index
            # page_size = min(200, max_results - len(papers))
            search_url = f"{self.search_url}advanced?advanced=&terms-0-operator=AND&terms-0-term={category}&terms-0-field=all&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=specific_year&date-year={year}&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order=-announced_date_first"
            
            logger.debug(f"Fetching URL: {search_url}")
            
            try:
                response = requests.get(search_url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    logger.error(f"Search failed. Status code: {response.status_code}")
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('li', {'class': 'arxiv-result'})
                
                logger.debug(f"Found {len(results)} results on this page")
                
                if not results:
                    logger.info("No more results found")
                    break

                for result in results:
                    if len(paper_ids) >= max_results:
                        break
                        
                    paper_id = self._extract_paper_id(result)
                    paper_ids.append(paper_id)

                    # if paper_id:
                        # logger.debug(f"Processing paper {paper_id}")
                        # paper_details = self.get_paper_details(paper_id)
                        # if paper_details:
                            # papers.append(paper_details)
                        # time.sleep(0.5)  
                
                # Move to next page
                start += len(results)
                
                if len(results) < 200:
                    break
                    
                # time.sleep(1)  # Delay between pages
            
            except Exception as e:
                logger.error(f"Error searching papers: {str(e)}")
                break
        
        logger.info(f"Completed search for {category}. Found {len(paper_ids)} papers")
        return paper_ids

    def _extract_paper_id(self, result_element: BeautifulSoup) -> Optional[str]:
        """Extract paper ID from a search result element."""
        # Look for the paper link
        link = result_element.find('p', {'class': 'list-title'})
        if link:
            a_tag = link.find('a')
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href']
                if '/abs/' in href:
                    # Extract ID from URL like /abs/2301.00001
                    paper_id = href.split('/abs/')[-1]
                    return paper_id
        return None

# Example usage:
if __name__ == "__main__":
    # Initialize the scraper
    scraper = ArxivScraper()
    
    # Categories to crawl
    categories = ["cs.LG"]
    years = [2020]  
    MAX_RESULTS = 10
    all_papers = []

    # Fetch papers for each category
    for (cat, year) in zip(categories, years):
        print(f"\nSearching category: {cat}")
        papers = scraper.search_by_category(cat, year, max_results=MAX_RESULTS)
        all_papers.extend(papers)
        print(f"✅ Found {len(papers)} papers in {cat}")

    print(all_papers)