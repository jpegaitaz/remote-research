import arxiv
import json
import os
from typing import List
from fastmcp import FastMCP  # ✅ Streamable HTTP-compatible MCP server

PAPER_DIR = "papers"

# ✅ Initialize FastMCP for Render deployment (streamable HTTP)
mcp = FastMCP("research", stateless_http=False)

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search arXiv for papers by topic and store results.
    """
    client = arxiv.Client()
    search = arxiv.Search(query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    papers = client.results(search)

    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        papers_info[paper.get_short_id()] = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }

    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"Results are saved in: {file_path}")
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Extract details of a specific paper across saved topics.
    """
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
    return f"No saved information found for paper ID: {paper_id}."

@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    Return a list of all available saved topic folders.
    """
    folders = []
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            if os.path.isdir(os.path.join(PAPER_DIR, topic_dir)):
                if os.path.exists(os.path.join(PAPER_DIR, topic_dir, "papers_info.json")):
                    folders.append(topic_dir)

    content = "# Available Topics\n\n"
    content += "\n".join(f"- {folder}" for folder in folders) or "No topics found."
    if folders:
        content += f"\n\nUse @{folders[0]} to access papers in that topic."
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Show all saved papers for a specific topic.
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry running `search_papers(topic='{topic}')` first."

    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)

        content = f"# Papers on {topic.replace('_', ' ').title()}\n\nTotal papers: {len(papers_data)}\n\n"
        for paper_id, info in papers_data.items():
            content += f"""## {info['title']}
- **Paper ID**: {paper_id}
- **Authors**: {', '.join(info['authors'])}
- **Published**: {info['published']}
- **PDF URL**: [{info['pdf_url']}]({info['pdf_url']})

### Summary
{info['summary'][:500]}...

---\n"""
        return content
    except json.JSONDecodeError:
        return f"# Error: Failed to load paper data for topic '{topic}'."

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate an LLM prompt to search and summarize academic research."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. 

Follow these instructions:
1. Search using: `search_papers(topic='{topic}', max_results={num_papers})`
2. Extract and organize:
   - Title
   - Authors
   - Publication Date
   - Key Findings Summary
   - Main Contributions
   - Methodologies
   - Relevance to '{topic}'
3. Provide:
   - Research overview
   - Common themes & trends
   - Gaps / future directions
   - Most impactful papers

Structure with headers & bullet points for clarity."""

# ✅ Run as HTTP server (for Render or local testing)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(mcp.app, host="0.0.0.0", port=port)

