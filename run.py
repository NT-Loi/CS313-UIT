from scraper import ArxivScraper, GoogleScholarScraper, HuggingFaceScraper
from semanticscholar import SemanticScholar # API

arxiv_scraper = ArxivScraper()
categories = ["cs"] 
years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]  
MAX_RESULTS = 1
all_papers = []

# Fetch papers for each category
for cat in categories:
    for year in years: 
        print(f"Searching category: {cat}")
        papers = arxiv_scraper.search_by_category(cat, year, max_results=MAX_RESULTS)
        all_papers.extend(papers)
        print(f"\tFound {len(papers)} papers in {cat}")
        break
    break

hf_scraper = HuggingFaceScraper()
for paper in all_papers:
    arxiv_id = paper['arxiv_id']
    hf_res = hf_scraper.get_paper_details(arxiv_id)
    paper.update(hf_res)
    print(paper)

# ggs_scraper = GoogleScholarScraper(headless=False) # Please remains headless=False solve CAPTCHA
# for paper in all_papers:
#     # print(paper)
#     try:
#         arxiv_id = paper['arxiv_id']
#         ggs_res = ggs_scraper.get_paper_details(arxiv_id, include_citations_over_time=False)
#     except Exception as e:
#         print(f"Unexpected error: {str(e)}")
#         import traceback
#         traceback.print_exc()
#     finally:
#         ggs_scraper.close()
    
#     paper.update(ggs_res)
#     print(paper)