import requests
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import re

logger = logging.getLogger("arxiv_crawler")
logging.basicConfig(
    filename='arxiv.log',             
    encoding='utf-8',
    level=logging.DEBUG,                 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ArxivScraper:
    def __init__(self):
        # Initialize the scraper with base URLs and headers for HTTP requests.
        # The headers mimic a browser to avoid being blocked by arXiv.
        self.base_url = "https://arxiv.org/abs/"
        self.search_url = "https://arxiv.org/search/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """
        Fetch paper details from arXiv using the paper ID.

        Args:
            paper_id (str): The arXiv paper ID (e.g., '2301.00001').

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
            "categories": categories.get('categories')
        }
            
        # except Exception as e:
        #     logger.error(f"Error fetching paper {paper_id}: {str(e)}")
        #     return None

    def _get_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the paper title from the HTML content.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the paper page.

        Returns:
            str: The title of the paper, or an empty string if not found.
        """
        title_element = soup.find('h1', {'class': 'title mathjax'})
        if title_element:
            return title_element.text.replace('Title:', '').strip()
        return ''

    def _get_authors(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract the list of authors from the HTML content.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the paper page.

        Returns:
            List[str]: A list of author names, or an empty list if not found.
        """
        authors_div = soup.find('div', {'class': 'authors'})
        if authors_div:
            return [author.text.strip() for author in authors_div.find_all('a')]
        return []

    def _get_abstract(self, soup: BeautifulSoup) -> str:
        """
        Extract the abstract of the paper from the HTML content.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the paper page.

        Returns:
            str: The abstract of the paper, or an empty string if not found.
        """
        abstract_element = soup.find('blockquote', {'class': 'abstract mathjax'})
        if abstract_element:
            return abstract_element.text.replace('Abstract:', '').strip()
        return ''

    def _get_categories(self, soup):
        """
        Extract the primary and additional categories of the paper.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the paper page.

        Returns:
            dict: A dictionary containing the primary category and a list of all categories.
        """
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
        """
        Extract submission history details, including published date, last revised date, and number of revisions.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the paper page.

        Returns:
            dict: A dictionary containing submission history details.
        """
        raw_text = soup.find('div', {'class': 'dateline'}).text
        submission_info = {
        'published_date': None,
        'last_revised_date': None,
        'num_revisions': 0
        }

        # Regex patterns
        submitted_pattern = re.search(r'Submitted on ([0-9]{1,2} [A-Za-z]+ [0-9]{4}) \(v(\d+)\)', raw_text)
        revised_pattern = re.search(r'last revised ([0-9]{1,2} [A-Za-z]+ [0-9]{4}) .*v(\d+)\)', raw_text)

        date_format = "%d %b %Y"  # e.g., "1 Jul 2025"

        # Extract submission info
        if submitted_pattern:
            published_date = datetime.strptime(submitted_pattern.group(1), date_format)
            submission_info['published_date'] = published_date
            first_version = int(submitted_pattern.group(2))
        else:
            first_version = 1

        # Extract revision info (if exists)
        if revised_pattern:
            last_revised_date = datetime.strptime(revised_pattern.group(1), date_format)
            last_version = int(revised_pattern.group(2))
        else:
            last_revised_date = submission_info['published_date']
            last_version = first_version

        submission_info['last_revised_date'] = last_revised_date
        submission_info['num_revisions'] = max(0, last_version - first_version)

        return submission_info

    def search_by_category(self, category: str, year: int = 2020, max_results: int = 10) -> List[Dict]:
        """
        Search for papers in a specific category and year.

        Args:
            category (str): The arXiv category (e.g., 'cs.AI').
            year (int): The year to filter papers by (default is 2020).
            max_results (int): Maximum number of results to return (default is 10).

        Returns:
            List[Dict]: A list of dictionaries containing paper details.
        """
        
        papers = []
        start = 0
        
        logger.info(f"Starting search for category {category}, max_results={max_results}")
        
        while len(papers) < max_results:
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
                    if len(papers) >= max_results:
                        break
                        
                    paper_id = self._extract_paper_id(result)
                    if paper_id:
                        logger.debug(f"Processing paper {paper_id}")
                        paper_details = self.get_paper_details(paper_id)
                        if paper_details:
                            papers.append(paper_details)
                        # time.sleep(0.5)  
                
                # Move to next page
                start += len(results)
                
                if len(results) < 200:
                    break
                    
                # time.sleep(1)  # Delay between pages
            
            except Exception as e:
                logger.error(f"Error searching papers: {str(e)}")
                break
        
        logger.info(f"Completed search for {category}. Found {len(papers)} papers")
        return papers

    def _extract_paper_id(self, result_element: BeautifulSoup) -> Optional[str]:
        """
        Extract the arXiv paper ID from a search result element.

        Args:
            result_element (BeautifulSoup): A search result element containing paper details.

        Returns:
            Optional[str]: The arXiv paper ID, or None if not found.
        """
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
    MAX_RESULTS = 30
    all_papers = []

    # Fetch papers for each category
    for (cat, year) in zip(categories, years):
        print(f"\nSearching category: {cat}")
        papers = scraper.search_by_category(cat, year, max_results=MAX_RESULTS)
        all_papers.extend(papers)
        print(f"✅ Found {len(papers)} papers in {cat}")

    print(f"\n{'='*60}")
    print(f"✅ Total papers fetched: {len(all_papers)}")
    print("="*60)
    
    # Display sample results
    if all_papers:
        print("\nSample papers:")
        for i, paper in enumerate(all_papers[:3], 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   ID: {paper['id']}")
            print(f"   Authors: {', '.join(paper['authors'][:2])}{'...' if len(paper['authors']) > 2 else ''}")
            print(f"   Published: {paper['published']}")