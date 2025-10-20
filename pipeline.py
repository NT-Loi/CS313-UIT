# from multiprocessing import Pool
from scraper import ArxivScraper, GoogleScholarScraper, HuggingFaceScraper, SemanticScholarAPI
import json
from datetime import datetime
import os
from pathlib import Path
import re

class ScraperPipeline:
    def __init__(self, output_basedir: str = 'data', num_workers: int = 4):
        self.output_basedir = output_basedir
        Path(self.output_basedir).mkdir(parents=True, exist_ok=True)
        self.num_workers = num_workers # useless for now
        self.arxiv_scraper = ArxivScraper()
        self.hf_scraper = HuggingFaceScraper()
        self.ss_scraper = SemanticScholarAPI()
        self.processed_file = self.output_basedir + f'/processed.json'
        self.processing_file = self.output_basedir + f'/processing.json'

        existing_ids = []
        for filename in os.listdir(self.output_basedir):
            if filename.endswith('.json'):
                paper_id = re.match(r'(\d{4}\.\d{5})\.json', filename)
                if paper_id:
                    existing_ids.append(paper_id.group(1))
        with open(self.processed_file, 'w', encoding='utf-8') as id_file:
            json.dump({'arxiv_id': existing_ids,
                       'timestamp': datetime.now().isoformat()}, 
                      id_file, ensure_ascii=False, indent=4)
        self.existing_ids = existing_ids

    def default_converter(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    def get_paper_details(self, paper_id: str) -> dict[str, any]:
        paper = self.arxiv_scraper.get_paper_details(paper_id)
        
        hf_res = self.hf_scraper.get_paper_details(paper_id)

        if hf_res is None:
            print(f"HuggingFaceScraper: Failed to fetch paper {paper_id}")
            return None

        paper.update(hf_res)
        
        ggs_scraper = GoogleScholarScraper(headless=False)  # Please remains headless=False solve CAPTCHA
        # print(ggs_scraper.have_cookies)
        if ggs_scraper.have_cookies == True:
            ggs_scraper.load_cookies_from_file("cookies.pkl")
        try:
            ggs_res = ggs_scraper.get_paper_details(paper_id)
            if ggs_res is None:
                print(f"GoogleScholarScraper: Failed to fetch paper {paper_id}")
                return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
        ggs_scraper.close()
        paper.update(ggs_res)
        del ggs_scraper

        ss_res = self.ss_scraper.get_paper_details(paper_id)
        if ss_res is None:
            print(f"SemanticScholarAPI: Failed to fetch paper {paper_id}")
            return None
        for key, value in ss_res.items():
            if key != 'authors' and key!= 'citationCount':
                paper[key] = value
        return paper

    def __call__(self, arxiv_id: str = None, category: str = None,  year: int = None, max_results: int = 100):
        if arxiv_id:
            paper = self.get_paper_details(arxiv_id)
            if paper is None:
                # print(f"Failed to fetch paper {arxiv_id}")
                return None
            with open(self.output_basedir+f'/{arxiv_id}.json', 'w', encoding='utf-8') as file:
                json.dump(paper, file, ensure_ascii=False, indent=4, default=self.default_converter)
            return paper

        if os.path.exists(self.processing_file):
            print(f"Resuming from {self.processing_file}")
            with open(self.processing_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                paper_ids = data.get('arxiv_id', [])
        else:
            print("Starting search for paper IDs from Arxiv")
            paper_ids = self.arxiv_scraper.search_by_category_year(category, year, max_results=max_results)
            with open(self.processing_file, 'w', encoding='utf-8') as file:
                json.dump({'arxiv_id':paper_ids, 
                           'timestamp': datetime.now().isoformat()}, 
                          file, ensure_ascii=False, indent=4)
            print(f"Found {len(paper_ids)} paper IDs from Arxiv")

        if not paper_ids:
            print("No paper IDs to process. Exiting.")
            os.remove(self.processing_file)
            return
        
        paper_ids = list(set(paper_ids) - set(self.existing_ids))
        
        if not paper_ids:
            print("All paper IDs have been processed. Try increase max_results.")
            os.remove(self.processing_file)
            return
        print(f"Processing {len(paper_ids)} unprocessed paper IDs")

        for paper_id in paper_ids:
            # Loi: I have tried to use multiprocessing 
            #      but it seems that google captcha cannot be handled well in multiple processes :(
            # with Pool(processes=self.num_workers) as pool:
            #     enriched_papers = pool.map(self.enrich, batch)

            print(f"Processing paper ID: {paper_id}")
            paper = self.get_paper_details(paper_id)
            if paper is None:
                # print(f"Failed to fetch paper {paper_id}")
                continue

            processing = []
            with open(self.processing_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                processing = data['arxiv_id']
            processing.remove(paper_id)
            if processing is None:
                os.remove(self.processing_file)
            else:
                with open(self.processing_file, 'w', encoding='utf-8') as file:
                    json.dump({'arxiv_id':processing, 
                            'timestamp': datetime.now().isoformat()}, 
                            file, ensure_ascii=False, indent=4)

            self.existing_ids.append(paper_id)
            with open(self.processed_file, 'w', encoding='utf-8') as id_file:
                json.dump({'arxiv_id': self.existing_ids,
                           'timestamp': datetime.now().isoformat()}, 
                            id_file, ensure_ascii=False, indent=4)

            with open(self.output_basedir+f'/{paper_id}.json', 'w', encoding='utf-8') as file:
                json.dump(paper, file, ensure_ascii=False, indent=4, default=self.default_converter)

if __name__ == '__main__':
    pipeline = ScraperPipeline()
    category = "cs" 
    year = 2017  
    # pipeline(category=category, year=year, max_results=1250)
    pipeline(arxiv_id="1712.06951")