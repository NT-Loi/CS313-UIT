from semanticscholar import SemanticScholar

class SemanticScholarAPI():
    def __init__(self):
        self.scraper = SemanticScholar()

    def get_paper_details(self, arxiv_id: str):
        try:
            api_res = self.scraper.get_paper(
            f'arXiv:{arxiv_id}',
            fields=["externalIds", "publicationVenue",
                    "citationCount","referenceCount","influentialCitationCount",
                    "citations.citationCount", "citations.referenceCount",
                    "references.citationCount", "references.referenceCount"]
            )
        except Exception as e:
            return None
        api_res = dict(api_res)
        # return api_res
        def extract_citation_info(entry):
            ext_ids = entry.get('externalIds') or {}
            return {
                'arxiv_id': ext_ids.get('ArXiv'),
                'referenceCount': entry.get('referenceCount'),
                'citationCount': entry.get('citationCount'),
                'influentialCitationCount': entry.get('influentialCitationCount')
            }

        # Local references for faster attribute access
        citations = api_res.get('citations', [])
        references = api_res.get('references', [])
        # authors = api_res.get('authors', [])
        venue = api_res.get('publicationVenue', {}) or {}

        return {
            'venue': {
                'name': venue.get('name'),
                'type': venue.get('type')
            },
            'citationCount': api_res.get('citationCount'),
            'citations': [extract_citation_info(c) for c in citations],
            # 'citations': api_res.get('citations'),
            'referenceCount': api_res.get('referenceCount'),
            'references': [extract_citation_info(r) for r in references],
            # 'references': api_res.get('references'),
            'influentialCitationCount': api_res.get('influentialCitationCount'),
            'embedding': api_res.get('embedding'),
            # 'authors': authors
        }

if __name__ == '__main__':
    ss_scraper = SemanticScholarAPI()

    paper = ss_scraper.get_paper_details('2508.07049')
    # print(paper)
    import json
    with open('test.json', 'w', encoding='utf-8') as file:
        json.dump(paper, file, ensure_ascii=False, indent=4, default=str)