# AI-Powered Fact Checking System

An evidence-based AI fact verification system that retrieves relevant information, ranks evidence semantically, applies Natural Language Inference (NLI), and classifies factual claims as:

- **SUPPORTED**
- **REFUTED**
- **INSUFFICIENT**

Developed by **Kanishk Sharma**

**GitHub:** https://github.com/Kanish-777  
**Email:** [kanishsharma305@gmail.com](mailto:kanishsharma305@gmail.com)

<!-- Add the deployed application link here after deployment:
**Live Demo:** https://your-deployed-project-url
-->


## Project Overview

The **AI-Powered Fact Checking System** is designed to verify factual claims using evidence retrieved from external knowledge sources.

Instead of relying only on keyword matching or simple majority voting across websites, the system evaluates multiple factors including:

- Evidence relevance
- Semantic similarity
- Source credibility
- Natural Language Inference
- Evidence diversity
- Evidence sufficiency
- Supporting and contradicting evidence
- Final decision confidence

The project is implemented as a complete software application with:

- FastAPI backend
- HTML, CSS and JavaScript frontend
- SQLite claim history
- BGE semantic retrieval
- Cross-Encoder reranking
- DeBERTa-based Natural Language Inference
- Evidence filtering and aggregation
- Grounded explanation generation


## System Workflow

```text
User Claim
    ↓
Claim Cleaning
    ↓
Domain Detection
    ↓
Query Generation
    ↓
Evidence Retrieval
    ↓
Text Chunking
    ↓
Lexical Candidate Prefilter
    ↓
BGE Semantic Ranking
    ↓
Cross-Encoder Reranking
    ↓
Entity Filtering
    ↓
Evidence Diversity
    ↓
DeBERTa NLI Verification
    ↓
Factuality / Context Checks
    ↓
Evidence Sufficiency
    ↓
Score Aggregation
    ↓
Final Verdict
    ↓
Explanation Generation
```

The final verdict is displayed through the web interface together with:

- Model confidence score
- Support score
- Refute score
- Insufficient score
- Generated search queries
- Retrieved evidence
- Evidence sources
- Explanation


## Technologies Used

### Backend

- Python
- FastAPI
- Pydantic
- SQLite

### AI / NLP

- PyTorch
- Hugging Face Transformers
- Sentence Transformers
- BGE embeddings
- Cross-Encoder reranking
- DeBERTa Natural Language Inference

### Retrieval Sources

- Wikipedia
- Europe PMC for scientific and health-related evidence

### Frontend

- HTML
- CSS
- JavaScript

### Development Tools

- Visual Studio Code
- Git
- GitHub


## AI Models

### Semantic Retrieval

Model:

```text
BAAI/bge-base-en-v1.5
```

BGE is used to measure semantic similarity between generated search queries and candidate evidence passages.

Before BGE inference, a lightweight lexical prefilter reduces the number of candidate passages that need expensive semantic processing.


### Cross-Encoder Reranking

Model:

```text
cross-encoder/ms-marco-MiniLM-L6-v2
```

After initial BGE retrieval, the Cross-Encoder performs a more precise query-passage relevance evaluation.

This helps remove weaker evidence and prioritize passages that are more directly related to the claim.


### Natural Language Inference

Model:

```text
MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli
```

The NLI model evaluates the relationship between each claim and its retrieved evidence.

It produces probabilities for:

```text
Entailment
Neutral
Contradiction
```

These signals are converted into evidence-level decisions:

```text
SUPPORTED
REFUTED
INSUFFICIENT
```


## Evidence Retrieval

The system generates multiple search queries from the original claim.

For general factual claims, evidence is retrieved from Wikipedia.

For relevant scientific and health-related claims, the system can additionally retrieve evidence from Europe PMC.

The Wikipedia retrieval pipeline includes:

- Search query expansion
- Retry handling
- Rate-limit handling
- Concurrent page downloads
- Full-page extraction
- In-memory request caching
- Duplicate page handling


## Evidence Processing

Retrieved documents are divided into smaller sentence-aware passages.

The evidence pipeline then performs:

1. Lexical candidate prefiltering
2. BGE semantic ranking
3. Cross-Encoder reranking
4. Relevance thresholding
5. Entity filtering
6. Document diversity filtering
7. Natural Language Inference


## Evidence Sufficiency

The system does not force every claim into SUPPORTED or REFUTED.

If sufficiently strong and relevant evidence cannot be retrieved, the system can return:

```text
INSUFFICIENT
```

This conservative behavior helps reduce unsupported conclusions when reliable evidence is unavailable.


## Source-Aware Aggregation

The final verdict is not generated using simple website majority voting.

The system considers factors such as:

- NLI confidence
- Semantic relevance
- Cross-Encoder relevance score
- Source credibility
- Evidence diversity
- Evidence sufficiency
- Supporting evidence
- Contradictory evidence

This allows stronger evidence to have greater influence than weak or indirectly related information.


## Explanation Generation

After determining the final verdict, the system identifies strong verified evidence and produces a grounded explanation.

Example:

```text
The claim "The Sun is a planet" is refuted by the retrieved evidence.
The strongest contradictory evidence comes from "Sun", which provides
factual information directly inconsistent with the claim.
```

The explanation is generated from evidence already processed by the verification pipeline rather than from an unsupported free-form answer.


## Claim History

The application includes SQLite-based claim history.

For each successful fact check, the system stores:

- Claim
- Final verdict
- Model confidence
- Explanation
- Claim domain
- Timestamp

Users can view previously checked claims through the frontend and can clear the stored history.


## Web Interface

The frontend provides:

- Claim input
- Character counter
- Loading state
- Processing timer
- Verdict badge
- Model confidence score
- Support / Refute / Insufficient scores
- Generated search queries
- Expandable evidence cards
- Direct source links
- Claim history
- How-the-system-works section
- Responsive layout

The frontend communicates directly with the FastAPI backend using HTTP API requests.


## API Endpoints

### Check a Claim

```http
POST /check-claim
```

Example request:

```json
{
    "claim": "The Sun is a planet"
}
```

### Claim History

```http
GET /history
```

### Clear Claim History

```http
DELETE /history
```

### Health Check

```http
GET /health
```

### FastAPI Documentation

```text
/docs
```


## Final Evaluation

The completed system was evaluated using a fresh holdout set of:

```text
24 claims
```

The set was balanced across all three verdict classes:

```text
8 SUPPORTED
8 REFUTED
8 INSUFFICIENT
```

Final results:

```text
Correct predictions: 21 / 24
Accuracy: 87.50%
Runtime errors: 0
```

The three incorrect cases were false claims where the system returned **INSUFFICIENT** instead of **REFUTED**.

This indicates that the system behaved conservatively when sufficiently strong contradictory evidence was not retrieved rather than producing a confident unsupported verdict.

The detailed evaluation output is available in:

```text
final_evaluation_results.json
```


## Performance Optimization

The system is designed to run on CPU hardware and includes several optimizations:

- Lexical candidate prefiltering
- Limited BGE candidate set
- Batched NLI inference
- Concurrent Wikipedia page retrieval
- In-memory retrieval caching
- Cross-Encoder filtering
- Evidence diversity filtering

Actual response time varies depending on:

- Wikipedia API latency
- Wikipedia rate limiting
- Number of retrieved pages
- Number of candidate passages
- CPU inference performance
- Network conditions


## Project Structure

```text
AI_fact_checker/
│
├── frontend/
│   └── index.html
│
├── models/
│   ├── __init__.py
│   └── schemas.py
│
├── services/
│   ├── __init__.py
│   ├── claim_service.py
│   ├── comparison_reasoner.py
│   ├── cross_encoder_reranker.py
│   ├── domain_router.py
│   ├── entity_filter.py
│   ├── evidence_diversity.py
│   ├── evidence_retriever.py
│   ├── evidence_sufficiency.py
│   ├── explanation_generator.py
│   ├── factuality_guard.py
│   ├── history_database.py
│   ├── news_retriever.py
│   ├── nli_verifier.py
│   ├── query_generator.py
│   ├── scientific_retriever.py
│   ├── semantic_ranker.py
│   ├── source_credibility.py
│   ├── text_processor.py
│   └── verdict_aggregator.py
│
├── data/
│   └── SQLite database created at runtime
│
├── evaluation_runner.py
├── unseen_evaluation_runner.py
├── final_evaluation_runner.py
├── final_evaluation_results.json
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```


## Running the Project Locally

### 1. Clone the repository

```bash
git clone <repository-url>
```

### 2. Move into the project directory

```bash
cd AI_fact_checker
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Start the FastAPI application

```bash
python -m uvicorn main:app --reload
```

### 7. Open the application

```text
http://127.0.0.1:8000/
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```


## Current Limitations

The system currently has several practical limitations:

- External evidence retrieval requires internet connectivity.
- Wikipedia may temporarily rate-limit repeated requests.
- CPU inference can require several seconds per claim.
- Retrieval quality directly affects verification quality.
- Some false claims can return INSUFFICIENT when strong contradictory evidence is not retrieved.
- The displayed confidence value is a model/aggregation score and should not be interpreted as a calibrated probability of absolute factual certainty.
- External knowledge sources may change over time.


## Future Improvements

Possible future improvements include:

- Persistent evidence retrieval caching
- Additional trusted evidence sources
- Better claim decomposition
- Improved scientific evidence retrieval
- Source-specific credibility modelling
- Claim-level confidence calibration
- Asynchronous request processing
- GPU-accelerated inference
- Cloud database integration
- User authentication
- Larger benchmark evaluations
- Improved deployment scalability


## Developer

**Kanishk Sharma**

GitHub:  
https://github.com/Kanish-777

Email:  
[kanishsharma305@gmail.com](mailto:kanishsharma305@gmail.com)