# Implementation Notes & Technical Decisions

## Technical Decisions

### 1. Vector Database Selection: FAISS vs Server-based Vector DBs
- **Decision**: Implemented `faiss-cpu` with persistent `index.faiss` and `metadata.json`.
- **Rationale**: Keeps the application completely self-contained, light on system resources (optimized for 8 GB RAM local development), and eliminates external server overhead or container orchestration dependencies.

### 2. Sentence-Boundary Aware Chunking
- **Chunk Size**: 700 characters
- **Chunk Overlap**: 100 characters
- **Rationale**: 700 characters (~100-120 words) provides optimal context window resolution for webpage sections (e.g. executive bios, product features) without overwhelming embedding vector space or exceeding LLM context boundaries.

### 3. SSRF & Ingestion Security
- Enforced strict hostname resolution checks prior to initiating HTTP GET requests.
- Blocked internal loopbacks (`127.0.0.1`), LAN subnets (`192.168.x.x`, `10.x.x.x`), and `.local`/`.internal` top-level domains to protect internal networks.

### 4. Grounded Context & Anti-Hallucination Controls
- System prompt instructs the LLM model to strictly disclaim when query context is missing or irrelevant rather than fabricating information.
- Every citation explicitly attaches document ID, page title, match score percentage, and source URL link.
