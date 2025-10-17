from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
            paper_info['citations'] = 0
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
                        paper_info['citations'] = int(numbers[0])
                    
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
    
    def get_citations_over_time(self, cited_by_url): # FIXIT
        """
        Get citations per year from the 'Cited by' page
        
        Args:
            cited_by_url: URL to the 'Cited by' page
        
        Returns:
            dict: Citations per year {year: count}
        """
        try:
            
            # Navigate to cited by page
            self.browser.get(cited_by_url)
            self.human_like_delay(3, 5)
            
            # Check if we hit a CAPTCHA
            if self.check_captcha():
                logging.info("Continuing after CAPTCHA solved...")
            
            citations_by_year = {}
            
            # Wait for page to load - try multiple selectors
            page_loaded = False
            wait_selectors = [
                (By.ID, 'gs_res_ccl_mid'),
                (By.ID, 'gs_res_ccl'),
                (By.CLASS_NAME, 'gs_r')
            ]
            
            for selector_type, selector_value in wait_selectors:
                try:
                    WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    page_loaded = True
                    break
                except:
                    continue
            
            if not page_loaded:
                logging.warning("Page may not have loaded properly")
            
            # Try to find the citation graph
            graph_found = False
            
            # Method 1: Look for the histogram graph (most common)
            try:
                graph_container = self.browser.find_element(By.ID, 'gsc_oci_graph_bars')
                bars = graph_container.find_elements(By.CLASS_NAME, 'gsc_oci_g_t')
                
                logging.info(f"  ✓ Found {len(bars)} year entries in graph")
                
                for bar in bars:
                    try:
                        # The structure is usually: <a class="gsc_oci_g_t"><span class="gsc_oci_g_al">YEAR</span></a>
                        year_elem = bar.find_element(By.CLASS_NAME, 'gsc_oci_g_al')
                        year = year_elem.text.strip()
                        
                        # Get the z-index value which represents citation count
                        a_elem = bar.find_element(By.XPATH, './ancestor::a[@class="gsc_oci_g_t"]')
                        
                        # The count is in a nearby span with class gsc_oci_g_a
                        try:
                            count_elem = a_elem.find_element(By.CSS_SELECTOR, 'span.gsc_oci_g_a')
                            count_text = count_elem.text.strip()
                            
                            if count_text and count_text.isdigit():
                                citations_by_year[year] = int(count_text)
                                logging.info(f"  {year}: {count_text} citations")
                                graph_found = True
                        except:
                            # Try to get from z-index style
                            style = a_elem.get_attribute('style')
                            z_match = re.search(r'z-index:\s*(\d+)', style)
                            if z_match:
                                count = int(z_match.group(1))
                                citations_by_year[year] = count
                                logging.info(f"  {year}: {count} citations")
                                graph_found = True
                    except Exception as e:
                        continue
                
            except NoSuchElementException:
                logging.info("  ⚠ Citation graph not found (Method 1)")
            except Exception as e:
                logging.info(f"  ⚠ Error with Method 1: {str(e)}")
            
            # Method 2: Alternative structure
            if not graph_found:
                try:
                    # Sometimes the data is in a different structure
                    year_spans = self.browser.find_elements(By.CSS_SELECTOR, 'span.gsc_oci_g_al')
                    
                    for year_span in year_spans:
                        year = year_span.text.strip()
                        
                        # Navigate up to find the count
                        parent = year_span.find_element(By.XPATH, './ancestor::a')
                        count_spans = parent.find_elements(By.CSS_SELECTOR, 'span.gsc_oci_g_a')
                        
                        for count_span in count_spans:
                            count_text = count_span.text.strip()
                            if count_text.isdigit():
                                citations_by_year[year] = int(count_text)
                                logging.info(f"  {year}: {count_text} citations")
                                graph_found = True
                                break
                        
                except Exception as e:
                    logging.info(f"  ⚠ Method 2 failed: {str(e)}")
            
            # Method 3: Extract from JavaScript data
            if not graph_found:
                try:
                    logging.info("  → Trying to extract from page source...")
                    page_source = self.browser.page_source
                    
                    # Look for patterns like: [2017,150],[2018,200]
                    pattern = r'\[(\d{4}),(\d+)\]'
                    matches = re.findall(pattern, page_source)
                    
                    if matches:
                        for year, count in matches:
                            if 1900 < int(year) < 2100:  # Sanity check
                                citations_by_year[year] = int(count)
                                logging.info(f"  {year}: {count} citations")
                        graph_found = True
                except Exception as e:
                    logging.info(f"  ⚠ Method 3 failed: {str(e)}")
            
            if not citations_by_year:
                logging.info("\n  ✗ Could not extract citation data")
                logging.info("  Possible reasons:")
                logging.info("    - Paper has no citations")
                logging.info("    - Page structure changed")
                logging.info("    - Anti-bot detection")
                logging.info("    - Citations not shown in graph format")
                
                # Save screenshot for debugging
                self.browser.save_screenshot('debug_citations.png')
                logging.info("  → Screenshot saved as 'debug_citations.png'")
            else:
                total = sum(citations_by_year.values())
                logging.info(f"\n✓ Extracted {len(citations_by_year)} years, Total: {total} citations")
            
            return citations_by_year
            
        except TimeoutException:
            logging.info("  ✗ Timeout loading cited by page")
            return {}
        except Exception as e:
            logging.error(f"Error extracting citations over time: {str(e)}")
            import traceback
            traceback.print_exc()
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
            'citations': 0
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
                citations_by_year = self.get_citations_over_time(paper_info['cited_by_url'])
                
                # Navigate back to search results
                self.browser.back()
                self.human_like_delay(2, 4)
            
            results['citations_by_year'] = citations_by_year
        
        results['citations'] = paper_info['citations']

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
        results = scraper.get_paper_details(arxiv_id, include_citations_over_time=False)
        print(results)
    finally:
        scraper.close()