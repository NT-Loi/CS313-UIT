from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import random
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("google_scholar")
logging.basicConfig(
    filename='google_scholar.log',
    encoding='utf-8',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
def extract_citation_data_as_dict(html: str) -> dict:
    """
    Trích xuất năm và số lượng trích dẫn từ mã HTML và trả về dưới dạng
    một dictionary (year: citations).
    
    Args:
        html (str): Chuỗi HTML chứa dữ liệu biểu đồ Google Scholar.
        
    Returns:
        dict: Dictionary với key là năm (int) và value là số lượng trích dẫn (int).
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Tìm tất cả các thẻ <a> chứa data-year và data-count
    citation_elements = soup.find_all('a', class_='gs_hist_g_a')

    # Sử dụng dictionary để lưu trữ dữ liệu (Năm -> Citations)
    citation_dict = {}

    for element in citation_elements:
        year_str = element.get('data-year')
        count_str = element.get('data-count')

        if year_str and count_str:
            try:
                # Chuyển đổi sang kiểu số nguyên
                year = int(year_str)
                count = int(count_str)
                # Thêm vào dictionary
                citation_dict[year] = count
            except ValueError:
                # Bỏ qua nếu giá trị không hợp lệ
                continue

    return citation_dict

class GoogleScholarScraper:
    """
    Google Scholar scraper using Selenium with anti-detection measures
    """
    
    def __init__(self, headless=False):
        """
        Initialize the scraper
        
        Args:
            headless: If True, run browser in headless mode (no visible window)
        """
        self.browser = self._setup_browser(headless)
    
    def _setup_browser(self, headless):
        """Setup Chrome browser with anti-detection options"""
        chrome_options = Options()
        
        # Anti-detection measures
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        
        # User agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if headless:
            chrome_options.add_argument('--headless')
        
        browser = webdriver.Chrome(options=chrome_options)
        browser.maximize_window()
        
        # Remove webdriver property to avoid detection
        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        return browser
    
    def human_like_delay(self, min_sec=2, max_sec=5):
        """Add random delay to mimic human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def type_like_human(self, element, text):
        """Type text slowly like a human"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def check_captcha(self):
        """Detect if a Google CAPTCHA or 'unusual traffic' page is shown."""
        html = self.browser.page_source.lower()

        # Common text patterns in CAPTCHA or block pages
        patterns = [
            "unusual traffic",
            "our systems have detected",
            "sorry, we can't process your request",
            "to continue, please type the characters below",
            'id="captcha"',
            "please show you're not a robot",
            "/sorry/index",
            "recaptcha"
        ]

        if any(p in html for p in patterns):
            logging.warning("⚠️ Google detected a CAPTCHA!")
            logging.warning("Please solve it manually in the browser window.")
            
            # Pause until user confirms solving it
            input("Press Enter after solving CAPTCHA...")
            return True
        
        return False

    def search_paper(self, arxiv_id):
        """
        Search for a paper by ArXiv ID
        
        Args:
            arxiv_id: The ArXiv ID of the paper
        
        Returns:
            dict: Paper information with title, authors, citations
        """
        try:
            logging.info(f"Searching for paper: {arxiv_id}")
            
            # Navigate to Google Scholar
            self.browser.get('https://scholar.google.com/')
            self.human_like_delay(2, 4)
            
            # Check if we hit a CAPTCHA
            if self.check_captcha():
                logging.info("Continuing after CAPTCHA solved...")
            
            # Find search box - try multiple selectors
            search_box = None
            selectors = ['q', 'gs_hp_box']
            
            for selector in selectors:
                try:
                    search_box = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.NAME, selector))
                    )
                    break
                except:
                    try:
                        search_box = self.browser.find_element(By.ID, selector)
                        break
                    except:
                        continue
            
            if not search_box:
                # Try finding by CSS selector
                search_box = self.browser.find_element(By.CSS_SELECTOR, 'input[type="text"]')
            
            # Type search query slowly
            search_query = f'arxiv:{arxiv_id}'
            self.type_like_human(search_box, search_query)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results to load
            self.human_like_delay(3, 5)
            
            # Check if we hit a CAPTCHA
            if self.check_captcha():
                logging.info("Continuing after CAPTCHA solved...")
            
            # Try multiple selectors for results
            first_result = None
            result_selectors = [
                (By.CSS_SELECTOR, 'div.gs_ri'),
                (By.CSS_SELECTOR, 'div.gs_r'),
                (By.CLASS_NAME, 'gs_ri'),
                (By.XPATH, '//div[@class="gs_ri"]')
            ]
            
            for selector_type, selector_value in result_selectors:
                try:
                    first_result = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except:
                    continue
            
            if not first_result:
                return None
            
            # Extract paper information
            paper_info = {}
            
            # Title - try multiple selectors
            title_selectors = ['h3.gs_rt', 'h3.gs_rt a', '.gs_rt', 'h3 a']
            for selector in title_selectors:
                try:
                    title_elem = first_result.find_element(By.CSS_SELECTOR, selector)
                    paper_info['title'] = title_elem.text.strip()
                    if paper_info['title']:
                        break
                except:
                    continue
            
            if not paper_info.get('title'):
                paper_info['title'] = 'N/A'
                        
            # Citations - try multiple approaches
            paper_info['citationCount'] = 0
            paper_info['cited_by_url'] = None
            
            citation_selectors = [
                ".//a[contains(text(), 'Cited by')]",
                ".//a[contains(@href, 'cites=')]",
                ".//a[contains(text(), 'cited by')]",
                ".//a[contains(text(), 'Được trích dẫn bởi')]"  # Vietnamese
            ]
            
            for selector in citation_selectors:
                try:
                    citation_elem = first_result.find_element(By.XPATH, selector)
                    citations_text = citation_elem.text
                    # Extract number from text
                    numbers = re.findall(r'\d+', citations_text)
                    if numbers:
                        paper_info['citationCount'] = int(numbers[0])
                    
                    paper_info['cited_by_url'] = citation_elem.get_attribute('href')
                    break
                except:
                    continue
            
            # Get author profile links
            # Find the author container div
            author_div = first_result.find_element(By.CLASS_NAME, 'gs_fmaa')

            paper_info['author_profiles'] = []

            # Step 1: Extract inner HTML to process both linked and unlinked authors
            html_content = author_div.get_attribute("innerHTML")

            # Step 2: Split by commas safely
            parts = re.split(r',\s*', html_content.strip())

            for part in parts:
                part = part.strip()

                # Case 1: linked author
                if "<a" in part:
                    try:
                        temp_soup = BeautifulSoup(part, "html.parser")
                        a_tag = temp_soup.find("a")
                        name = a_tag.text.strip()
                        href = a_tag.get("href", None)
                    except Exception:
                        name, href = None, None
                else:
                    # Case 2: plain text (no <a> tag)
                    name = BeautifulSoup(part, "html.parser").text.strip()
                    href = None
                if name: 
                    paper_info['author_profiles'].append({
                        "name": name,
                        "url": href
                    })

            
            # COMMENT: conference/journal name on scholar is inconsistent, hard to parse
            # info_div = first_result.find_element(By.CLASS_NAME, 'gs_fma_p')

            return paper_info
            
        except TimeoutException:
            logging.error(f"Timeout error when searching paper: {str(e)}")
            self.browser.save_screenshot('debug_timeout.png')
            logging.debug("Screenshot saved as 'debug_timeout.png'")
            return None
        except Exception as e:
            logging.error(f"Error searching paper: {str(e)}")
            self.browser.save_screenshot('debug_error.png')
            logging.debug("Error. Screenshot saved as 'debug_error.png'")
            import traceback
            traceback.print_exc()
            return None

    def get_citations_over_time(self, cited_by_url: str) -> dict:
        try:
            url_plot_citations_per_year = cited_by_url + "#d=gs_md_hist&t="

            logging.info(f"Opening cited-by histogram URL: {url_plot_citations_per_year}")
            # Open the cited-by page with the histogram fragment
            self.browser.get(url_plot_citations_per_year)

            # Wait a short while for dynamic content to load
            self.human_like_delay(2, 4)
            
            # Try to locate the histogram container. Google Scholar uses 'gs_md_hist' id
            try:
                hist_elem = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.ID, 'gs_md_hist'))
                    )
                html = hist_elem.get_attribute('innerHTML')
            except Exception:
                # Fallback: use full page source
                logging.debug('Histogram element not found; falling back to full page source')
                html = self.browser.page_source

            # Parse HTML into citation dict
            citation_dict = extract_citation_data_as_dict(html)

            logging.info(f"Extracted citation years: {sorted(citation_dict.keys())}")
            return citation_dict
        except Exception as e:
            logging.error(f"Error getting citations over time: {str(e)}")
            return {}
    
    def get_author_stats(self, author_url, author_name):
        """
        Get statistics from an author's profile
        
        Args:
            author_url: URL to the author's Google Scholar profile
            author_name: Name of the author
        
        Returns:
            dict: Author statistics including h-index
        """
        try:            
            # Open profile in new tab
            self.browser.execute_script("window.open(arguments[0]);", author_url)
            self.browser.switch_to.window(self.browser.window_handles[-1])
            
            # Wait for profile to load
            self.human_like_delay(3, 5)
            
            # Check if we hit a CAPTCHA
            if self.check_captcha():
                logging.info("Continuing after CAPTCHA solved...")
            
            # Wait for statistics table
            stats_table = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.ID, 'gsc_rsb_st'))
            )
            
            # Get all stat values
            stat_values = stats_table.find_elements(By.CLASS_NAME, 'gsc_rsb_std')
            
            author_stats = {'name': author_name}
            
            if len(stat_values) >= 6:
                # Row 1: Citations (All, Since 2020)
                author_stats['citations_all'] = int(stat_values[0].text)
                author_stats['citations_recent'] = int(stat_values[1].text)
                
                # Row 2: h-index (All, Since 2020)
                author_stats['h_index_all'] = int(stat_values[2].text)
                author_stats['h_index_recent'] = int(stat_values[3].text)
                
                # Row 3: i10-index (All, Since 2020)
                author_stats['i10_index_all'] = int(stat_values[4].text)
                author_stats['i10_index_recent'] = int(stat_values[5].text)
                
            # Close tab and return to main window
            self.browser.close()
            self.browser.switch_to.window(self.browser.window_handles[0])
            
            return author_stats
            
        except TimeoutException:
            if len(self.browser.window_handles) > 1:
                self.browser.close()
                self.browser.switch_to.window(self.browser.window_handles[0])
            return {'name': author_name, 'error': 'Timeout'}
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            if len(self.browser.window_handles) > 1:
                self.browser.close()
                self.browser.switch_to.window(self.browser.window_handles[0])
            return {'name': author_name, 'error': str(e)}
    
    def get_paper_details(self, arxiv_id, include_citations_over_time=True):
        """
        Get paper citation and h-index for all authors
        
        Args:
            arxiv_id: The ArXiv ID of the paper
            include_citations_over_time: If True, also extract citations per year
        
        Returns:
            dict: Complete results with paper info and author h-indices
        """
        results = {
            'arxiv_id': arxiv_id,
            # 'paper': None,
            'authors': [],
            'citations_by_year': {},
            'citationCount': 0
        }
        
        # Step 1: Search for the paper
        paper_info = self.search_paper(arxiv_id)
        if not paper_info:
            logging.info("Could not retrieve paper information")
            return results
        
        # results['paper'] = paper_info
        
        # Step 2: Get citations over time if requested
        if include_citations_over_time:
            if paper_info.get('cited_by_url'):
                # print(paper_info['cited_by_url'])
                citations_by_year = self.get_citations_over_time(paper_info['cited_by_url'])
                
                # Navigate back to search results
                self.browser.back()
                self.human_like_delay(2, 4)
            
            results['citations_by_year'] = citations_by_year
        
        results['citationCount'] = paper_info['citationCount']

        # Step 3: Get h-index for each author with a profile
        author_profiles = paper_info.get('author_profiles', [])
        
        for idx, author_profile in enumerate(author_profiles):            
            # COMMENT: AN AUTHOR HAS NO 'url' MEANS THAT HE/SHE DOESN'T HAVE A SCHOLAR ACCOUNT.
            
            if author_profile['url']:
                author_stats = self.get_author_stats(
                    author_profile['url'], 
                    author_profile['name']
                )
                results['authors'].append(author_stats)
                
                # Delay between authors to avoid rate limiting
                if idx < len(author_profiles) - 1:  # Don't delay after last author
                    self.human_like_delay(3, 6)

            else: 
                results['authors'].append({'name': author_profile['name'], 'citations_all': None, 'citations_recent': None, 
                                           'h_index_all': None, 'h_index_recent': None, 'i10_index_all': None, 'i10_index_recent': None})
        return results
    
    def close(self):
        """Close the browser"""
        if self.browser:
            self.browser.quit()

# Example usage
if __name__ == "__main__":    
    # Initialize scraper
    scraper = GoogleScholarScraper(headless=False)  # Set to True to hide browser
    
    try:
        # Example: "Attention is All You Need" paper
        arxiv_id = "1706.03762"
        
        # Get paper and author information (including citations over time)
        results = scraper.get_paper_details(arxiv_id, include_citations_over_time=True)
        print(results)
    finally:
        scraper.close()