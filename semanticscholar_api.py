import requests, json
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

if not API_KEY:
    print("Warning: SEMANTIC_SCHOLAR_API_KEY not set. You may be subject to rate limiting.")

headers = {"x-api-key": API_KEY} if API_KEY else {}


def fetch_papers_bulk(ids, fields="venue,referenceCount,embedding"):
    """Fetch a batch of papers from Semantic Scholar and return the Response."""
    payload = {"ids": ids}
    params = {"fields": fields}
    resp = requests.post(
        "https://api.semanticscholar.org/graph/v1/paper/batch",
        params=params,
        json=payload,
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_citations_byid(arxiv_id: str, limit: int = 10):

    url = f"https://api.semanticscholar.org/graph/v1/paper/{arxiv_id}/citations"
    fields = "paperId,contexts,isInfluential"

    params = {"limit": limit,"fields": fields}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()  

r = fetch_papers_bulk([
    "ARXIV:2106.15928",
    "ARXIV:2203.15267",
])
citation = fetch_citations_byid("ARXIV:2203.15267")
print(json.dumps(r, indent=2))
print(json.dumps(citation, indent=2))
# Example output:
# [ 
#   {
#     "paperId": "f712fab0d58ae6492e3cdfc1933dae103ec12d5d",
#     "venue": "",
#     "referenceCount": 13,
#     "embedding": {
#       "model": "specter_v1",
#       "vector": [
#         -1.873365044593811,
#         -7.963120460510254,
#         ...,
#         -2.1540238857269287
#       ]
#     }
#   },
#   {
#     "paperId": "00d502b795239e43f0dfca94a00cf0d3260020fb",
#     "venue": "Journal of machine learning research",
#     "referenceCount": 104,
#     "embedding": {
#       "model": "specter_v1",
#       "vector": [
#         -4.190493106842041,
#         -2.795156955718994,
#         ...,
#         -1.5015684366226196
#       ]
#     }
#   }
# ]
print("vector dimension is",len(r[1]["embedding"]["vector"]))
# vector dimension is 768