# AI Agent Instructions for Daily News Summary Project

This file documents the architectural decisions and future implementation plans agreed upon by the user. Any future modifications to the logic in `api/llm_utils.py` or the summarization pipeline should adhere to these guidelines.

## Future Architecture: Enhanced Summarization Pipeline

The goal is to move away from a simple "all-in-one" summarization to a structured, cluster-based approach with quality control, while respecting Vercel's serverless timeout limits.

### 1. Core Workflow
The process should follow a **Map-Reduce** inspired approach combined with **Chain of Thought (CoT)** prompting to minimize API round-trips.

1.  **Data Input:**
    *   Fetch all articles for the day from the Database.
    *   English titles are already translated to Traditional Chinese by the scraper (ensure this is maintained).

2.  **Processing (Single or Dual Pass LLM Call):**
    *   **Step 1: Clustering & Selection**
        *   Group articles based on **semantic similarity of titles**.
        *   **Priority Rule:** Articles from source **"BlockTempo" (動區)** must be prioritized as a Main Topic if possible.
        *   **Relevance Rule:** For other sources, prioritize topics with high financial impact or broad relevance.
        *   Identify "Main Topics" (Clusters) vs. "Other News" (Isolated/Low priority items).

    *   **Step 2: Summarization with Maker-Checker (Self-Reflexion)**
        *   *To avoid timeouts, this should ideally be combined with Step 1 or run as a single optimized prompt if token limits allow. If split, ensure total duration < 60s.*
        *   **Maker:** Generate a summary for each Main Topic cluster using the full content of the articles.
        *   **Checker (Self-Correction):** The model must perform a self-check on the generated summaries:
            *   **(A) Hallucination Check:** Does the summary contain facts not present in the source text?
            *   **(B) Consistency Check:** Does the summary accurately reflect the titles and content of the group?
        *   **Refinement:** Output the corrected summary if the Checker finds issues.

3.  **Output Structure:**
    *   **Main Topics:** Detailed summaries of the identified clusters.
    *   **Other News:** A list of titles/links for the remaining articles, without full summaries.

### 2. Technical Constraints
*   **Platform:** Vercel Serverless Functions.
*   **Timeout:** Hard limit of roughly **60 seconds** (Pro plan) or **10 seconds** (Hobby plan) for the response.
*   **Strategy:** Prefer **Chain of Thought (CoT)** in a single comprehensive prompt over multiple sequential API calls to reduce latency and network overhead.

### 3. Source Handling
*   **Translation:** International sources (BBC, CNN, Reuters, NYT, TechCrunch, Forbes, Axios, Business Insider) must have their titles translated to Traditional Chinese **before** saving to the DB. (Implemented in `scrapers.py`).
