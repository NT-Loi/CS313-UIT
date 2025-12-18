import json
from pipeline import ScraperPipeline
import os

for y in range(2012, 2025):
    base_dir = f"data (Copy)/{y}"
    paper_files = os.listdir(base_dir)

    sp = ScraperPipeline()

    for paper_file in paper_files:
        paper_id =  paper_file.replace('.json', '')
        with open(base_dir+f"/{paper_file}", 'r', encoding='utf-8') as f:
            paper = json.load(f)
        # Validate required fields
        required_fields = ['arxiv_id', 'title', 'abstract', 'authors', 'categories', 'published_date', 'num_revisions', 'references']
        for field in required_fields:
            if field not in paper or paper[field] in [None, '', [], {}]:
                # if field != 'references':
                #     print(f"Paper {paper_id} is missing required field: {field}.")
                #     continue
                print(f"Paper {paper_id} is missing required field: {field}. Dropping...")
                try:
                    os.remove(base_dir+f"/{paper_file}")
                except FileNotFoundError:
                    continue