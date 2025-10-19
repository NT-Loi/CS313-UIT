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
from collections import defaultdict

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

def to_int(s: str) -> int:
    # "1,234" -> 1234 ; "12 345" -> 12345
    if s is None:
        return None
    s = s.replace(",", "").replace(" ", "")
    m = re.search(r"\d+", s)
    return int(m.group(0)) if m else None

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
        """
        Extract {year: citations} from Google Scholar 'Cited by' / paper view.
        Ưu tiên con số hiển thị; fallback sang z-index khi cần.
        """
        try:
            self.browser.get(cited_by_url)
            self.human_like_delay(3, 5)

            # CAPTCHA gate
            if self.check_captcha():
                logging.info("Continuing after CAPTCHA solved...")

            citations_by_year = {}
            graph_found = False

            # ===== 1) Đợi trang tải (thử nhiều selector) =====
            wait_selectors = [
                (By.ID, "gs_res_ccl_mid"),
                (By.ID, "gs_res_ccl"),
                (By.CLASS_NAME, "gs_r"),
                # vùng biểu đồ trong trang chi tiết bài (paper overlay)
                (By.ID, "gsc_oci_graph_bars"),
            ]
            page_loaded = False
            for stype, sval in wait_selectors:
                try:
                    WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((stype, sval))
                    )
                    page_loaded = True
                    break
                except Exception:
                    continue
            if not page_loaded:
                logging.info(" Page may not have loaded fully; continue with best effort.")

            # 2) Tìm container biểu đồ (nhiều khả năng nhất) 
            containers = []
            # (a) giấy/bài: overlay container
            try:
                c = self.browser.find_element(By.ID, "gsc_oci_graph_bars")
                containers.append(c)
            except NoSuchElementException:
                pass

            # (b) phương án khác: toàn bộ trang, rồi quét các anchor/cot bar
            if not containers:
                containers = [self.browser]  # quét rộng

            #3) Quét các cột năm trong mỗi container
            temp_map = defaultdict(int)  # year(int) -> count (lấy max nếu trùng)

            for root in containers:
                # Các anchor-bar phổ biến trong biểu đồ
                # (class 'gsc_oci_g_t' là thẻ <a> mỗi năm; bên trong có span năm 'gsc_oci_g_al'
                #  và thường có span số 'gsc_oci_g_a'; nếu không có, fallback style/z-index)
                bars = root.find_elements(By.CSS_SELECTOR, "a.gsc_oci_g_t")
                if not bars:
                    # dự phòng: có site dùng span trực tiếp
                    bars = root.find_elements(By.CSS_SELECTOR, ".gsc_oci_g_t, .gsc_oci_g_b, span.gsc_oci_g_al")

                if bars:
                    logging.info(f"✓ Found {len(bars)} bar-like elements")
                else:
                    logging.info("⚠ No bar-like elements found in this container")
                    continue

                for bar in bars:
                    year, count = None, None

                    # (1) Lấy năm từ text/span
                    try:
                        # phổ biến: <a class="gsc_oci_g_t"><span class="gsc_oci_g_al">2019</span>...</a>
                        year_elem = None
                        try:
                            year_elem = bar.find_element(By.CLASS_NAME, "gsc_oci_g_al")
                            year = to_int(year_elem.text.strip())
                        except Exception:
                            # dự phòng: nếu bar chính là span gsc_oci_g_al
                            if bar.get_attribute("class") and "gsc_oci_g_al" in bar.get_attribute("class"):
                                year = to_int(bar.text.strip())

                        # fallback nữa: đọc aria-label nếu có
                        if year is None:
                            aria = bar.get_attribute("aria-label") or ""
                            # pattern kiểu "2019: 25 citations"
                            m = re.search(r"(19|20)\d{2}", aria)
                            if m:
                                year = int(m.group(0))
                    except Exception:
                        pass

                    # (2) Lấy count hiển thị nếu có 
                    try:
                        # thường là <span class="gsc_oci_g_a">25</span>
                        count_elem = None
                        try:
                            count_elem = bar.find_element(By.CSS_SELECTOR, "span.gsc_oci_g_a")
                            count = to_int(count_elem.text.strip())
                        except Exception:
                            # đôi khi count nằm trong aria-label: "2019: 25 citations"
                            aria = bar.get_attribute("aria-label") or ""
                            mm = re.search(r"(\d{4}).*?(\d+)", aria)
                            if mm:
                                # mm.group(1)=year, group(2)=count
                                if year is None:
                                    y = to_int(mm.group(1))
                                    if y:
                                        year = y
                                count = to_int(mm.group(2))
                    except Exception:
                        pass

                    # (3) Fallback: z-index trong style 
                    if count is None:
                        style = bar.get_attribute("style") or ""
                        # dạng "z-index: 25;" (đôi khi đặt trên phần tử con)
                        z = re.search(r"z-index\s*:\s*(\d+)", style)
                        if not z:
                            # thử phần tử con hay anh em gần đó
                            try:
                                # cột bar bên trong (nếu có)
                                inner = bar.find_element(By.CSS_SELECTOR, ".gsc_oci_g_b, *[style*='z-index']")
                                style2 = inner.get_attribute("style") or ""
                                z = re.search(r"z-index\s*:\s*(\d+)", style2)
                            except Exception:
                                z = None
                        if z:
                            count = int(z.group(1))

                    # Ghi kết quả (năm hợp lệ + count >= 0)
                    if year and (1900 < year < 2100) and (count is not None):
                        # Một số DOM trùng năm -> lấy MAX
                        temp_map[year] = max(temp_map[year], int(count))
                        graph_found = True

            # 4) Dự phòng cuối: regex toàn trang "[2017,150]" 
            if not graph_found:
                try:
                    page_source = self.browser.page_source
                    for y, c in re.findall(r"\[(\d{4}),\s*(\d+)\]", page_source):
                        y, c = int(y), int(c)
                        if 1900 < y < 2100:
                            temp_map[y] = max(temp_map[y], c)
                    graph_found = len(temp_map) > 0
                except Exception as e:
                    logging.info(f"Fallback regex failed: {e}")

            citations_by_year = {int(y): int(temp_map[y]) for y in sorted(temp_map.keys())}

            if not citations_by_year:
                # logging.info("\n✗ Could not extract citation data.")
                # logging.info("Possible reasons: no graph, DOM changed, anti-bot, or no citations.")
                self.browser.save_screenshot("debug_citations.png")
                # logging.info("→ Screenshot saved as 'debug_citations.png'")
            else:
                total = sum(citations_by_year.values())
                # logging.info(f"\n✓ Extracted {len(citations_by_year)} years, Total: {total} citations")

            return citations_by_year

        except TimeoutException:
            logging.info("Timeout loading cited by page")
            return {}
        except Exception as e:
            logging.info(f"Error extracting citations over time: {e}")
            import traceback; traceback.print_exc()
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
                print(paper_info['cited_by_url'])
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