from scraper import ArxivScraper, GoogleScholarScraper, HuggingFaceScraper, SemanticScholarAPI

# arxiv_scraper = ArxivScraper()
# categories = ["cs"] 
# years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]  
# MAX_RESULTS = 1
# all_papers = []

# # Fetch papers for each category
# for cat in categories:
#     for year in years: 
#         print(f"Searching category: {cat}")
#         papers = arxiv_scraper.search_by_category(cat, year, max_results=MAX_RESULTS)
#         all_papers.extend(papers)
#         print(f"\tFound {len(papers)} papers in {cat}")
#         break
#     break

arxiv_scraper = ArxivScraper()
all_papers = []
all_papers.append(arxiv_scraper.get_paper_details("2002.09132"))

hf_scraper = HuggingFaceScraper()
for paper in all_papers:
    arxiv_id = paper['arxiv_id']
    hf_res = hf_scraper.get_paper_details(arxiv_id)
    paper.update(hf_res)
    # print(paper)

ggs_scraper = GoogleScholarScraper(headless=False) # Please remains headless=False solve CAPTCHA
for paper in all_papers:
    # print(paper)
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
    # print(paper)

ss_scraper = SemanticScholarAPI()
for paper in all_papers:
    arxiv_id = paper['arxiv_id']
    ss_res = ss_scraper.get_paper_details(arxiv_id)
    for old_author, new_author in zip(paper['authors'], ss_res['authors']):
        old_author.update(new_author)
    for key, value in ss_res.items():
        if key != 'authors':
            paper[key] = value

from datetime import datetime

def default_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")

import json
with open('data.json', 'w', encoding='utf-8') as file:
    json.dump(all_papers, file, ensure_ascii=False, indent=4, default=default_converter)