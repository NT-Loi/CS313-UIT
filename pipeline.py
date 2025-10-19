# from multiprocessing import Pool
from scraper import ArxivScraper, GoogleScholarScraper, HuggingFaceScraper, SemanticScholarAPI
import json
from datetime import datetime
import os
from pathlib import Path

class ScraperPipeline:
    def __init__(self, output_basename: str = 'data', num_workers: int = 4):
        self.output_basename = output_basename
        Path(self.output_basename).mkdir(parents=True, exist_ok=True)
        self.num_workers = num_workers # useless for now
        self.arxiv_scraper = ArxivScraper()
        self.hf_scraper = HuggingFaceScraper()
        self.ss_scraper = SemanticScholarAPI()
        self.ids_file = self.output_basename + f'/{self.output_basename}_ids.json'

        try:       
            with open(self.ids_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.existing_ids = set(data['arxiv_id'])
        except Exception as e:
            self.existing_ids = set()
            with open(self.ids_file, 'w', encoding='utf-8') as file:
                json.dump({'arxiv_id': [],
                           'timestamp': datetime.now().isoformat(),
                           'num_new_papers': 0,
                           'version': 0}, file)   
                
    def default_converter(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    def remove_duplicates(self, paper_ids: list[str], papers: list[dict]) -> list[str]:
        paper_ids = set(paper_ids)
        new_ids = paper_ids - self.existing_ids
        new_papers = [paper for paper in papers if paper['arxiv_id'] in new_ids]
        return new_papers

    def fetch_arxiv_papers(self, arxiv_ids: list[str] = None, categories: list[str] = None, 
                           years: list[int] = None, max_results: int = 100) -> tuple[list[str], list[dict]]:
        if arxiv_ids:
            papers = [self.arxiv_scraper.get_paper_details(arxiv_id) for arxiv_id in arxiv_ids]
            return arxiv_ids, papers
        
        # Quite stupid, this nested for loop doesn't ensure max_results ---
        # I don't have time to refactor now
        all_papers = []
        for cat in categories:
            for year in years:
                papers = self.arxiv_scraper.search_by_category(cat, year, max_results=max_results)
                all_papers.extend(papers)

        paper_ids = [paper['arxiv_id'] for paper in all_papers]
        return paper_ids, all_papers

    def enrich(self, paper: dict[str, any]) -> dict[str, any]:
        arxiv_id = paper['arxiv_id']
        
        hf_res = self.hf_scraper.get_paper_details(arxiv_id)
        paper.update(hf_res)
        ggs_scraper = GoogleScholarScraper(headless=False)  # Please remains headless=False solve CAPTCHA
        try:
            ggs_res = ggs_scraper.get_paper_details(arxiv_id)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            ggs_scraper.close()
        paper.update(ggs_res)
        
        ss_res = self.ss_scraper.get_paper_details(arxiv_id)
        for key, value in ss_res.items():
            if key != 'authors' and key!= 'citationCount':
                paper[key] = value
        del ggs_scraper
        return paper

    def __call__(self, arxiv_id: str = None, categories: list[str] = None,  years: list[int] = None, 
                save_every: int = 20, max_results: int = 100):
        
        arxiv_ids, arxiv_papers = self.fetch_arxiv_papers(arxiv_id, categories, years, max_results)

        new_arxiv_papers = self.remove_duplicates(arxiv_ids, arxiv_papers)

        # batch processing
        batch_size = save_every
        for i in range(0, len(new_arxiv_papers), batch_size):
            batch = new_arxiv_papers[i:i+batch_size]

            # Loi: I have tried to use multiprocessing 
            #      but it seems that google captcha cannot be handled well in multiple processes :(
            # with Pool(processes=self.num_workers) as pool:
            #     enriched_papers = pool.map(self.enrich, batch)

            enriched_papers = []
            for paper in batch:
                enriched_paper = self.enrich(paper)
                enriched_papers.append(enriched_paper)

            old_version = None
            with open(self.ids_file, 'r', encoding='utf-8') as id_file:
                old_version = json.load(id_file).get('version', 0)

            curr_version = old_version + 1
            with open(self.ids_file, 'w', encoding='utf-8') as id_file:
                json.dump({'arxiv_id': list(self.existing_ids) + 
                           [paper['arxiv_id'] for paper in enriched_papers],
                           'timestamp': datetime.now().isoformat(),
                           'num_new_papers': len(enriched_papers),
                           'version': curr_version}, 
                            id_file, ensure_ascii=False, indent=4)

            with open(self.output_basename+f'/{self.output_basename}_'+str(int(curr_version))+'.json', 'w', encoding='utf-8') as file:
                json.dump(enriched_papers, file, ensure_ascii=False, indent=4, default=self.default_converter)

if __name__ == '__main__':
    pipeline = ScraperPipeline()
    categories = ["cs"] 
    years = [2017]  
    pipeline(categories=categories, years=years, save_every=1, max_results=1)