from scraper import ArxivScraper, GoogleScholarScraper
from semanticscholar import SemanticScholar

arxiv_scraper = ArxivScraper()
categories = ["cs"]  
MAX_RESULTS = 10
all_papers = []

# Fetch papers for each category
for cat in categories:
    print(f"Searching category: {cat}")
    papers = arxiv_scraper.search_by_category(cat, max_results=MAX_RESULTS)
    all_papers.extend(papers)
    print(f"\tFound {len(papers)} papers in {cat}")

ggs_scraper = GoogleScholarScraper(headless=False)
for paper in all_papers:
    try:
        arxiv_id = paper['arxiv_id']
        ggs_res = ggs_scraper.get_paper_details(arxiv_id, include_citations_over_time=False)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        ggs_scraper.close()
    
    paper.update(ggs_res)
    print(paper)