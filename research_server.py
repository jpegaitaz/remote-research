import os
import json
import arxiv
from typing import List
from fastestmcp import FastMCP

PAPER_DIR = "papers"

# ✅ Initialize MCP server (for HTTP clients like your chatbot)
mcp = FastMCP("research", stateless_http=False)

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
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
    Extract metadata about a saved paper.
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
    return f"There's no saved information related to paper {paper_id}."

@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders.
    """
    folders = []
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)

    content = "# Available Topics\n\n"
    content += "\n".join(f"- {folder}" for folder in folders) or "No topics found.\n"
    if folders:
        content += f"\n\nUse @{folders[0]} to access papers in that topic.\n"
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Return paper metadata for a specific topic.
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}"

    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)

        content = f"# Papers on {topic.title()}\n\nTotal: {len(papers_data)}\n\n"
        for paper_id, info in papers_data.items():
            content += f"""## {info['title']}
- **ID**: {paper_id}
- **Authors**: {', '.join(info['authors'])}
- **Published**: {info['published']}
- **PDF**: [{info['pdf_url']}]({info['pdf_url']})

**Summary:** {info['summary'][:400]}...

---
"""
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}"

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt for Claude to summarize academic papers."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the `search_papers` tool.

Then, extract and organize:
- Title, authors, date, key findings
- Methodology, innovations, relevance to '{topic}'

Finish with:
- A summary of research trends
- Gaps and future directions
- Notable impactful papers
"""

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(mcp.app, host="0.0.0.0", port=port)
