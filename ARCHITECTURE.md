# 🏗️ MEMORA - Complete Architecture & System Design

**Complete under-the-hood guide with all layers, concepts, and how everything works together**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Concepts](#core-concepts)
3. [Layer-by-Layer Architecture](#layer-by-layer-architecture)
4. [Data Models](#data-models)
5. [Detailed Feature Implementation](#detailed-feature-implementation)
6. [Storage & Indexing](#storage--indexing)
7. [Algorithms & Performance](#algorithms--performance)
8. [Integration Points](#integration-points)
9. [Error Handling & Resilience](#error-handling--resilience)
10. [Scalability & Limits](#scalability--limits)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEMORA SYSTEM v3.1.0                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUT STREAMS                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ • Ollama Chat (via proxy)  • File Ingestion  • Manual Chat      │  │
│  └──────────────┬───────────────────────────────────────────────────┘  │
│                 │                                                       │
│                 ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           INGESTION PIPELINE (Layer 4)                          │  │
│  │  ├─ Type Detection      (conversation/code/document)            │  │
│  │  ├─ Content Extraction  (human-readable strings)                │  │
│  │  ├─ Entity Recognition  (spaCy NER → Knowledge Graph)           │  │
│  │  ├─ PII Filtering       (sensitive data removal)                │  │
│  │  └─ Deduplication       (content hash check)                    │  │
│  └──────────────┬───────────────────────────────────────────────────┘  │
│                 │                                                       │
│                 ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           MEMORY CREATION (Layer 1 + Layer 4)                   │  │
│  │  ├─ Create Memory object  (with metadata)                       │  │
│  │  ├─ Link to Session       (group related memories)              │  │
│  │  ├─ Add to Knowledge Graph (entities & relationships)           │  │
│  │  └─ Trigger Indexing      (update all indices)                  │  │
│  └──────────────┬───────────────────────────────────────────────────┘  │
│                 │                                                       │
│                 ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           STORAGE LAYER (Layer 3)                               │  │
│  │  ├─ Compute SHA-256 hash (content addressing)                   │  │
│  │  ├─ Compress with zlib   (50% typical reduction)                │  │
│  │  ├─ Store in object store (.memora/objects/)                    │  │
│  │  ├─ Update all indices    (word, temporal, session, type)       │  │
│  │  ├─ Maintain LRU cache    (1000 most recent objects)            │  │
│  │  └─ Record in session     (session_id → memory_id mapping)      │  │
│  └──────────────┬───────────────────────────────────────────────────┘  │
│                 │                                                       │
│                 ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           SESSION MANAGEMENT (Layer 4)                          │  │
│  │  ├─ Keep session open     (buffer incoming memories)            │  │
│  │  ├─ Track session state   (active/closed)                       │  │
│  │  └─ Auto-commit on close  (create commit record)                │  │
│  └──────────────┬───────────────────────────────────────────────────┘  │
│                 │                                                       │
│                 ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           VERSION CONTROL (Layer 3)                             │  │
│  │  ├─ Create commit        (message + timestamp)                  │  │
│  │  ├─ Update branch ref    (point to new commit)                  │  │
│  │  ├─ Record in history    (timeline of all commits)              │  │
│  │  └─ Preserve all versions (for rollback)                        │  │
│  └──────────────┬───────────────────────────────────────────────────┘  │
│                 │                                                       │
│                 ▼                                                       │
│  MEMORY STORED & INDEXED ✓                                             │
│                                                                         │
│  SEARCH/QUERY OPERATIONS                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ User Query → Parse → Execute → Rank → Format → Display         │  │
│  │ (sub-100ms response time with full-text indexing)              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Memory (Core Entity)

A **Memory** is the atomic unit of information in Memora.

```python
@dataclass
class Memory:
    id: str                              # mem_<uuid> - unique identifier
    content: str                         # Human-readable text
    memory_type: MemoryType              # CONVERSATION | CODE | DOCUMENT
    confidence: float                    # 0.0-1.0 (how sure are we)
    source: MemorySource                 # OLLAMA_CHAT | FILE_INGESTION | MANUAL
    session_id: str                      # Which session created this
    branch: str                          # Which branch is this in
    turn_index: int                      # Order within session
    created_at: str                      # ISO 8601 timestamp
    updated_at: str                      # ISO 8601 timestamp
    supersedes: str | None               # mem_id of previous version (if updated)
    entities: list[str]                  # ["Python", "asyncio"] (from NER)
    metadata: dict                       # Extra fields
    pinned: bool                         # Always inject to LLM
    hidden: bool                         # Store but don't inject
```

**Why this design?**
- `id`: Content-addressable storage (find by hash)
- `branch`: Git-style isolation (different projects)
- `session_id`: Group related memories (single conversation)
- `entities`: Enable knowledge graph queries
- `supersedes`: Handle updates and conflicts
- `metadata`: Extensible for future features

### 2. Session (Context Grouping)

A **Session** groups related memories (typically one conversation).

```python
@dataclass
class Session:
    id: str                              # sess_<uuid>
    branch: str                          # Which branch
    created_at: str                      # When started
    closed_at: str | None                # When ended (None = active)
    memories: list[str]                  # [mem_id, mem_id, ...]
    source: MemorySource                 # How session was created
    metadata: dict                       # Custom data
```

**Why this design?**
- Groups related memories by conversation
- Enables "what did we discuss in session X" queries
- Can auto-commit when session closes
- Tracks which memories came together

### 3. Commit (Version Record)

A **Commit** records a point-in-time snapshot (Git-like).

```python
@dataclass
class Commit:
    id: str                              # mem_<timestamp>_<hash>
    branch: str                          # Which branch
    parent: str | None                   # Previous commit (for history)
    message: str                         # Commit message
    memories_added: list[str]            # [mem_id, ...]
    memories_removed: list[str]          # [mem_id, ...] (if rollback)
    timestamp: str                       # ISO 8601
    author: str                          # Who/what created this
```

**Why this design?**
- Enables full history and rollback
- Tracks what changed in each commit
- Parent reference creates commit chain
- Complete timeline of repository

### 4. Branch (Context Isolation)

A **Branch** isolates memories for different projects/topics.

```python
@dataclass
class Branch:
    name: str                            # "main", "feature/python", etc.
    head_commit: str                     # Current commit on this branch
    created_at: str                      # When created
    parent_branch: str | None            # Branched from which branch
    description: str                     # Optional description
    metadata: dict                       # Branch-specific data
```

**Why this design?**
- Isolates memories by project/topic
- Enables branching and merging patterns
- Tracks branch lineage
- Allows concurrent work on different contexts

### 5. GraphNode (Entity in Knowledge Graph)

A **GraphNode** represents an entity extracted from memories.

```python
@dataclass
class GraphNode:
    id: str                              # Entity name ("Python", "asyncio")
    category: str                        # "TECHNOLOGY", "CONCEPT", "PERSON"
    frequency: int                       # How many times mentioned
    first_seen: str                      # First mention timestamp
    last_seen: str                       # Most recent mention
    memories: list[str]                  # [mem_id, ...] mentioning this
    edges: dict[str, list[str]]          # {"connected_to": [node_id, ...]}
```

**Why this design?**
- Enables entity-based search
- Tracks concept relationships
- Shows learning progression (first_seen → last_seen)
- Enables graph traversal algorithms

---

## Layer-by-Layer Architecture

### Layer 1: Data Models

**Responsibility:** Define all data structures

**Components:**
```
memora/shared/models.py
├── Memory (content + metadata)
├── Session (groups memories)
├── Commit (version record)
├── Branch (project context)
├── GraphNode (entity)
├── Conflict (contradictions)
└── MemoryTree (hierarchical structure)
```

**Key Enums:**
```python
class MemoryType(Enum):
    CONVERSATION = "conversation"    # Chat exchange
    CODE = "code"                     # Source code
    DOCUMENT = "document"             # PDF/text/markdown

class MemorySource(Enum):
    OLLAMA_CHAT = "ollama_chat"       # Via proxy
    FILE_INGESTION = "file_ingestion" # Via ingest command
    MANUAL = "manual"                 # Via chat command

class ConflictType(Enum):
    TEMPORAL_SUPERSESSION = "temporal_supersession"  # New version
    SOURCE_CONFLICT = "source_conflict"              # Contradiction
    DIRECT_CONTRADICTION = "direct_contradiction"    # Opposite

class ConflictStatus(Enum):
    UNRESOLVED = "unresolved"
    AUTO_RESOLVED = "auto_resolved"
    USER_RESOLVED = "user_resolved"
```

**Validation:**
- Pydantic ensures type safety
- All dates are ISO 8601
- All IDs are guaranteed unique
- Content is never empty

---

### Layer 2: Integration Layer

**Responsibility:** Connect external systems (Ollama, file system)

#### 2.1: Ollama Proxy

**File:** `memora/ai/ollama_proxy.py`

**How it works:**
```
User Command
    ↓
User: "ollama run llama2"
    ↓
Client connects to http://localhost:11435 (Memora proxy)
    ↓
Memora Proxy
├─ Receives HTTP request
├─ Forwards to http://localhost:11434 (Real Ollama)
├─ Waits for response from Ollama
├─ Intercepts response stream
├─ Extracts conversation content
├─ Creates session (if new)
├─ Sends response back to client
└─ Streams all to Ingestion Pipeline
    ↓
Response flows to User (transparent)
    ↓
Meanwhile: Ingestion Pipeline processes asynchronously
```

**Technical Details:**
```python
class OllamaProxy:
    def __init__(self, proxy_port=11435, backend_port=11434):
        self.proxy_port = proxy_port
        self.backend_port = backend_port
        self.sessions = {}  # Active sessions
    
    async def handle_request(self, request):
        # 1. Identify or create session
        session_id = request.headers.get("X-Memora-Session-ID")
        if not session_id:
            session_id = generate_session_id()
        
        # 2. Forward to real Ollama
        response = await forward_to_ollama(request)
        
        # 3. Extract content from request/response
        prompt = extract_prompt(request)
        completion = extract_completion(response)
        
        # 4. Send to ingestion asynchronously
        asyncio.create_task(
            ingest_conversation(
                session_id=session_id,
                prompt=prompt,
                completion=completion
            )
        )
        
        # 5. Return response to client
        return response
```

**Key Features:**
- ✅ Transparent: Client sees no difference
- ✅ Asynchronous: Doesn't slow down chat
- ✅ Session tracking: Groups related exchanges
- ✅ Error recovery: Network issues don't break chat
- ✅ Fallbacks: If Ollama slow, proxy waits

#### 2.2: File Processing

**File:** `memora/ai/file_processor.py`

**Supported Formats:**
```
.py, .js, .ts, .go, .rs, .java    → Code extraction
.md, .txt, .rst                    → Text extraction
.pdf                               → PDF extraction (pypdf)
.docx (future)                     → Document extraction
```

**Processing Pipeline:**
```python
class FileProcessor:
    def process(self, file_path):
        # 1. Detect file type
        file_type = detect_type(file_path)  # → "code", "document", "text"
        
        # 2. Extract content
        if file_type == "code":
            content = extract_code(file_path)      # Comments + code
        elif file_type == "document":
            content = extract_text(file_path)      # Just text
        elif file_type == "pdf":
            content = extract_pdf(file_path)       # pypdf
        else:
            content = read_text(file_path)         # Fallback
        
        # 3. Detect encoding
        encoding = detect_encoding(content)  # chardet library
        content = content.decode(encoding) if bytes else content
        
        # 4. Split into memories
        memories = split_into_chunks(
            content=content,
            max_size=1000,  # ~1KB per memory
            split_on_boundaries=True  # Code blocks, paragraphs
        )
        
        # 5. Return list of Memory objects
        return [Memory(content=m, source=FILE_INGESTION) for m in memories]
```

---

### Layer 3: Storage & Indexing

**Responsibility:** Persistent storage, retrieval, and search indexing

#### 3.1: Git-Style Object Store

**File:** `memora/core/store.py`

**Design: Content-Addressed Storage**

```
Problem: How to store millions of memories efficiently?
Solution: Like Git - store by content hash

Benefits:
├─ Automatic deduplication (same content = same object)
├─ Integrity checking (can verify all objects)
├─ Efficient space usage (50% compression typical)
└─ Cross-platform (same hash regardless of OS)
```

**Structure:**
```
.memora/objects/
├── 1a/
│   ├── 2b3c4d5e6f7g8h9i0j.zlib   # Memory object
│   └── ...
├── 2b/
│   ├── 1a2b3c4d5e6f7g8h9i0j.zlib
│   └── ...
└── ... (one directory per first 2 hex digits of hash)
```

**Algorithm:**
```python
class ObjectStore:
    def write(self, memory: Memory) -> str:
        """Write memory to store, return object ID"""
        
        # 1. Serialize to JSON
        json_bytes = json.dumps(memory.to_dict()).encode('utf-8')
        
        # 2. Compute SHA-256 hash
        hash_digest = hashlib.sha256(json_bytes).hexdigest()
        # Example: "1a2b3c4d5e6f7g8h9i0j..."
        
        # 3. Compress
        compressed = zlib.compress(json_bytes)
        
        # 4. Determine path
        dir_path = f".memora/objects/{hash_digest[:2]}"
        file_path = f"{dir_path}/{hash_digest[2:]}.zlib"
        
        # 5. Write atomically
        create_dir(dir_path)
        write_atomic(file_path, compressed)  # Uses FileLock
        
        # 6. Update LRU cache
        self.cache[hash_digest] = memory
        if len(self.cache) > 1000:
            del self.cache[oldest_key]
        
        return hash_digest
    
    def read(self, object_id: str) -> Memory:
        """Read memory from store"""
        
        # 1. Check cache first
        if object_id in self.cache:
            return self.cache[object_id]
        
        # 2. Locate file
        file_path = f".memora/objects/{object_id[:2]}/{object_id[2:]}.zlib"
        
        # 3. Read and decompress
        compressed = read_file(file_path)
        json_bytes = zlib.decompress(compressed)
        
        # 4. Deserialize
        data = json.loads(json_bytes.decode('utf-8'))
        memory = Memory.from_dict(data)
        
        # 5. Update cache
        self.cache[object_id] = memory
        
        return memory
    
    def exists(self, object_id: str) -> bool:
        """Check if object exists without loading"""
        if object_id in self.cache:
            return True
        file_path = f".memora/objects/{object_id[:2]}/{object_id[2:]}.zlib"
        return os.path.exists(file_path)
```

**Key Properties:**
- ✅ Content-addressed: Same content always has same ID
- ✅ Compressed: ~50% space reduction
- ✅ Atomic: No partial writes
- ✅ Cached: LRU cache for hot objects
- ✅ Durable: ACID-like guarantees

#### 3.2: Multi-Dimensional Indexing

**File:** `memora/core/index.py`

**Four Indices for Different Query Types:**

##### Index 1: Word Index (Full-Text Search)

```python
# Structure: word → [memory_id, memory_id, ...]
word_index = {
    "python": ["mem_1", "mem_5", "mem_12"],
    "async": ["mem_3", "mem_7"],
    "function": ["mem_1", "mem_3", "mem_5"],
    ...
}

# Algorithm: Inverted Index
def index_memory(memory_id, content):
    words = tokenize(content)  # Remove stopwords, stem, etc.
    for word in words:
        if word not in word_index:
            word_index[word] = []
        word_index[word].append(memory_id)

# Search: BM25 Ranking
def search(query):
    query_words = tokenize(query)
    candidates = set()
    
    for word in query_words:
        if word in word_index:
            candidates.update(word_index[word])
    
    # Score with BM25
    scores = {}
    for mem_id in candidates:
        scores[mem_id] = bm25_score(mem_id, query_words)
    
    return sorted(scores, key=scores.get, reverse=True)[:20]
```

**Time Complexity:**
- Index write: O(n) where n = words in memory
- Index read: O(k) where k = results
- Search: ~1-10ms for typical queries

##### Index 2: Temporal Index (Time-Based Search)

```python
# Structure: Date → [memory_id, memory_id, ...]
temporal_index = {
    "2024-01-15": ["mem_1", "mem_2", "mem_3"],
    "2024-01-14": ["mem_4", "mem_5"],
    "2024-01-13": [],
    "2024-01-12": ["mem_6"],
    ...
}

# Search: Parse date query
def search_by_time(time_query):
    # Parse: "today", "last 7 days", "2024-01-15", "January 2024"
    start_date, end_date = parse_date_range(time_query)
    
    memories = []
    for date in date_range(start_date, end_date):
        if date in temporal_index:
            memories.extend(temporal_index[date])
    
    return memories
```

**Time Complexity:**
- Index write: O(1) hash lookup + append
- Time range query: O(days in range)

##### Index 3: Session Index (Context Search)

```python
# Structure: session_id → [memory_id, memory_id, ...]
session_index = {
    "sess_abc123": ["mem_1", "mem_2", "mem_3"],
    "sess_def456": ["mem_4", "mem_5", "mem_6"],
    ...
}

# Search: Get all memories from a session
def get_session_memories(session_id):
    return session_index.get(session_id, [])
```

##### Index 4: Type Index (Filter by Type)

```python
# Structure: type → [memory_id, memory_id, ...]
type_index = {
    "CONVERSATION": ["mem_1", "mem_3", "mem_5", ...],
    "CODE": ["mem_2", "mem_4", ...],
    "DOCUMENT": ["mem_6", ...],
}

# Search: Get all memories of type
def search_by_type(memory_type):
    return type_index.get(memory_type, [])
```

**Combined Search:**
```python
def search_advanced(
    query: str,
    time_range: str = None,
    memory_type: str = None,
    session_id: str = None
):
    # Start with full-text search
    candidates = word_index_search(query)
    
    # Filter by time if specified
    if time_range:
        time_memories = temporal_index_search(time_range)
        candidates = candidates & time_memories
    
    # Filter by type if specified
    if memory_type:
        type_memories = type_index_search(memory_type)
        candidates = candidates & type_memories
    
    # Filter by session if specified
    if session_id:
        session_memories = session_index_search(session_id)
        candidates = candidates & session_memories
    
    return candidates
```

**Performance:**
```
Full-text search:        5-50ms
Temporal search:         1-5ms
Combined search:         10-100ms
Database reads:          <1ms (cached)
Total latency:           <100ms
```

#### 3.3: Version Control (Commits & Branches)

**File:** `memora/core/refs.py` and `memora/core/branch_manager.py`

**Commit Structure:**
```python
class Commit:
    id: str = field(default_factory=lambda: f"mem_{timestamp()}_{random_hash()}")
    branch: str
    parent_commit: str | None  # Points to previous commit
    message: str
    memories_in_commit: list[str]  # All memories at this point
    timestamp: datetime
```

**Branch Tracking:**
```
.memora/refs/heads/
├── main                    # File contains: mem_abc123 (commit ID)
├── feature/python          # File contains: mem_def456
└── archived/old            # File contains: mem_ghi789
```

**Implementation:**
```python
class BranchManager:
    def switch_branch(self, branch_name: str):
        """Switch to a different branch"""
        if branch_name not in self.branches:
            raise BranchNotFoundError(f"Branch {branch_name} not found")
        
        # Read the head commit
        head_commit = read_file(f".memora/refs/heads/{branch_name}")
        
        # Load all memories in this commit and its ancestors
        current_memories = self.load_memories_at_commit(head_commit)
        
        # Update current branch pointer
        self.current_branch = branch_name
        self.current_commit = head_commit
        self.current_memories = current_memories
    
    def create_branch(self, branch_name: str, from_commit: str = None):
        """Create a new branch"""
        if branch_name in self.branches:
            raise BranchAlreadyExistsError(f"Branch {branch_name} exists")
        
        # Use current commit if not specified
        source_commit = from_commit or self.current_commit
        
        # Create branch file
        create_file(
            f".memora/refs/heads/{branch_name}",
            source_commit
        )
        
        self.branches[branch_name] = source_commit
    
    def commit(self, message: str, memories: list[Memory]):
        """Create a commit"""
        # Create commit record
        commit = Commit(
            branch=self.current_branch,
            parent_commit=self.current_commit,
            message=message,
            memories_in_commit=[m.id for m in memories],
            timestamp=now()
        )
        
        # Store commit in git-like object store
        commit_file = f".memora/objects/commits/{commit.id}.json"
        write_json(commit_file, commit)
        
        # Update branch ref
        write_file(
            f".memora/refs/heads/{self.current_branch}",
            commit.id
        )
        
        self.current_commit = commit.id
```

---

### Layer 4: Memory Management

**Responsibility:** Business logic for capturing, processing, and managing memories

#### 4.1: Ingestion Pipeline

**File:** `memora/core/ingestion.py`

**Pipeline Stages:**

```
Raw Input
    ↓
┌─ Type Detection
│  ├─ Pattern matching (is this code? conversation? document?)
│  ├─ Heuristics (has docstrings? Has "def"? → probably CODE)
│  └─ Fallback (if unsure, use heuristic)
│
├─ Content Extraction
│  ├─ For CODE: extract docstrings, comments, key functions
│  ├─ For CONVERSATION: parse prompt/completion pairs
│  ├─ For DOCUMENT: extract main text, ignore headers/footers
│  └─ Clean: remove noise, normalize whitespace
│
├─ Entity Recognition (NER)
│  ├─ Use spaCy language model
│  ├─ Extract: PERSON, ORG, PRODUCT, GPE, etc.
│  ├─ Also extract: code keywords, library names
│  └─ Store entities in Memory.entities list
│
├─ Knowledge Graph Update
│  ├─ Add entity nodes for new entities
│  ├─ Add edges between related entities
│  ├─ Update frequency counts
│  └─ Track first/last seen dates
│
├─ PII Filtering
│  ├─ Detect: email addresses, phone numbers, SSN, credit cards
│  ├─ Action: mask or remove
│  ├─ Log: what was removed
│  └─ Allow: user to configure sensitivity
│
├─ Deduplication
│  ├─ Compute content hash (SHA-256)
│  ├─ Check if hash exists
│  ├─ If exists: skip (don't add duplicate)
│  ├─ If new: continue to storage
│  └─ Update: if same content with different metadata, update
│
└─ Memory Creation
   ├─ Create Memory object with all extracted data
   ├─ Assign UUID
   ├─ Set timestamp
   ├─ Link to session/branch
   └─ Return to caller
```

**Implementation:**
```python
class IngestPipeline:
    def ingest(self, raw_content: str, source: MemorySource) -> Memory:
        # 1. Type Detection
        memory_type = self.detect_type(raw_content)
        
        # 2. Content Extraction
        extracted_content = self.extract_content(
            raw_content, 
            memory_type
        )
        
        # 3. Entity Recognition
        entities = self.extract_entities(extracted_content)
        
        # 4. PII Filtering
        filtered_content = self.filter_pii(extracted_content)
        
        # 5. Deduplication
        content_hash = hashlib.sha256(filtered_content.encode()).hexdigest()
        if self.store.exists(content_hash):
            return self.store.read(content_hash)  # Already have it
        
        # 6. Memory Creation
        memory = Memory(
            id=generate_memory_id(),
            content=filtered_content,
            memory_type=memory_type,
            source=source,
            entities=entities,
            created_at=now(),
            session_id=self.current_session_id,
            branch=self.current_branch,
        )
        
        return memory
```

#### 4.2: Session Management

**File:** `memora/core/session.py`

**Session Lifecycle:**

```
Session Creation
    ↓
Session ACTIVE
├─ User chatting / ingesting files
├─ Memories added to session
├─ Session buffering memories
└─ If timeout or explicit close → next
    ↓
Session CLOSING TRIGGER
├─ User stops chatting
├─ File ingestion completes
└─ Session timeout (configurable)
    ↓
Auto-Commit
├─ Bundle all memories in session
├─ Create commit record
├─ Update branch
└─ Session → CLOSED
    ↓
Session Archive
├─ Move session data to archive
├─ Keep reference in history
└─ Available for replay
```

**Implementation:**
```python
class SessionManager:
    def create_session(self, source: MemorySource) -> str:
        """Create a new session"""
        session_id = generate_session_id()  # sess_<uuid>
        
        session = Session(
            id=session_id,
            branch=self.current_branch,
            created_at=now(),
            source=source,
            memories=[]
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    def add_to_session(self, session_id: str, memory: Memory):
        """Add a memory to a session"""
        if session_id not in self.active_sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.memories.append(memory.id)
    
    def close_session(self, session_id: str, auto_commit: bool = True):
        """Close a session and optionally auto-commit"""
        if session_id not in self.active_sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        if auto_commit:
            # Create automatic commit
            commit = Commit(
                message=f"Auto-commit: {len(session.memories)} memories",
                memories_in_commit=session.memories,
                source=session.source,
            )
            self.store.write_commit(commit)
        
        # Archive session
        session.closed_at = now()
        self.closed_sessions[session_id] = session
        del self.active_sessions[session_id]
```

#### 4.3: Knowledge Graph

**File:** `memora/core/graph.py`

**Graph Construction:**

```
Named Entity Recognition (spaCy)
    ↓
Extract entities: [
    ("Python", "TECHNOLOGY"),
    ("asyncio", "LIBRARY"),
    ("function", "CONCEPT")
]
    ↓
Create/Update GraphNodes
├─ For each entity, find or create node
├─ Update frequency count
├─ Update last_seen timestamp
└─ Add memory to node's memory list
    ↓
Create Relationships
├─ Entities in same memory → connected
├─ Weight by frequency
├─ Type by relationship pattern
└─ Add to GraphNode.edges
    ↓
Knowledge Graph Complete
├─ Nodes: ~100-1000 entities
├─ Edges: ~500-5000 relationships
└─ Enables queries like "show me related to Python"
```

**Implementation:**
```python
class KnowledgeGraph:
    def extract_and_add(self, memory: Memory):
        """Extract entities and build graph"""
        
        # 1. Run NER
        doc = self.nlp(memory.content)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # 2. Create/update nodes
        for entity_text, entity_type in entities:
            entity_key = entity_text.lower()
            
            if entity_key not in self.nodes:
                self.nodes[entity_key] = GraphNode(
                    id=entity_key,
                    category=entity_type,
                    frequency=1,
                    first_seen=now(),
                    last_seen=now(),
                    memories=[memory.id]
                )
            else:
                node = self.nodes[entity_key]
                node.frequency += 1
                node.last_seen = now()
                node.memories.append(memory.id)
        
        # 3. Create relationships
        for i, ent1 in enumerate(entities):
            for ent2 in entities[i+1:]:
                # Entities in same memory are related
                key1 = ent1[0].lower()
                key2 = ent2[0].lower()
                
                if key1 in self.nodes:
                    if "related_to" not in self.nodes[key1].edges:
                        self.nodes[key1].edges["related_to"] = []
                    if key2 not in self.nodes[key1].edges["related_to"]:
                        self.nodes[key1].edges["related_to"].append(key2)
```

**Graph Queries:**
```python
def query_entity(self, entity: str, depth: int = 1):
    """Query an entity and its relationships"""
    
    entity_key = entity.lower()
    if entity_key not in self.nodes:
        return None
    
    node = self.nodes[entity_key]
    result = {
        "entity": node.id,
        "frequency": node.frequency,
        "first_seen": node.first_seen,
        "last_seen": node.last_seen,
        "memories": node.memories,
        "related": {}
    }
    
    # Traverse edges
    if depth > 0:
        for related_entity in node.edges.get("related_to", []):
            result["related"][related_entity] = {
                "frequency": self.nodes[related_entity].frequency,
                "last_mentioned": self.nodes[related_entity].last_seen
            }
    
    return result
```

---

### Layer 5: User Interface

**Responsibility:** Present features to users via CLI, API, Chat

#### 5.1: CLI (Command-Line Interface)

**File:** `memora/interface/cli.py`

**Technology:** Typer + Rich

```python
import typer
from rich.console import Console

app = typer.Typer(name="memora")
console = Console()

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, help="Number of results"),
    memory_path: str = typer.Option("./memora_data", help="Memory store path"),
):
    """Search memories by content"""
    engine = CoreEngine(memory_path)
    results = engine.search(query, limit=limit)
    
    # Format and display with Rich
    table = Table(title=f"Search Results: {query}")
    table.add_column("ID", style="cyan")
    table.add_column("Content", style="green")
    table.add_column("Type", style="magenta")
    
    for result in results:
        table.add_row(result.id, result.content[:100], result.memory_type)
    
    console.print(table)

@app.command()
def branch(
    action: str = typer.Argument(..., help="create|switch|list|delete"),
    name: str = typer.Argument(None, help="Branch name"),
    memory_path: str = typer.Option("./memora_data"),
):
    """Manage branches"""
    engine = CoreEngine(memory_path)
    
    if action == "list":
        branches = engine.list_branches()
        # Display as table
    elif action == "create":
        engine.create_branch(name)
    elif action == "switch":
        engine.switch_branch(name)
    # ... etc
```

**20+ Commands:**
```
Setup:     start, init, version, migrate
Search:    search, when, graph, graph query
Manage:    ingest, forget, chat, stats, where
Branch:    branch list, branch create, branch switch
History:   log, rollback, commit
Export:    export
Backup:    backup, restore
Optimize:  gc
Proxy:     proxy start, proxy stop, proxy status, proxy-setup
```

#### 5.2: REST API

**File:** `memora/interface/server.py`

**Technology:** FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Memora API")

@app.get("/memories/search")
async def search_memories(
    q: str,
    limit: int = 20,
    memory_path: str = "./memora_data"
):
    """Search memories"""
    engine = CoreEngine(memory_path)
    results = engine.search(q, limit=limit)
    return {"results": [r.to_dict() for r in results]}

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str, memory_path: str = "./memora_data"):
    """Get a specific memory"""
    engine = CoreEngine(memory_path)
    memory = engine.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404)
    return memory.to_dict()

@app.post("/memories")
async def create_memory(
    content: str,
    memory_type: str,
    memory_path: str = "./memora_data"
):
    """Create a memory manually"""
    engine = CoreEngine(memory_path)
    memory = engine.create_memory(content, memory_type)
    return memory.to_dict()

@app.get("/branches")
async def list_branches(memory_path: str = "./memora_data"):
    """List all branches"""
    engine = CoreEngine(memory_path)
    branches = engine.list_branches()
    return {"branches": branches}

# ... 20+ more endpoints
```

---

## Data Models

### Memory

```python
@dataclass
class Memory:
    # Identity
    id: str = field(default_factory=lambda: f"mem_{uuid4()}")
    
    # Content
    content: str  # Human-readable
    memory_type: MemoryType  # CONVERSATION | CODE | DOCUMENT
    
    # Source
    source: MemorySource  # OLLAMA_CHAT | FILE_INGESTION | MANUAL
    
    # Quality
    confidence: float = 0.95  # 0.0-1.0
    
    # Linking
    session_id: str  # Groups related memories
    branch: str  # Project context
    turn_index: int = 0  # Order in session
    
    # Timeline
    created_at: str = field(default_factory=lambda: now().isoformat())
    updated_at: str = field(default_factory=lambda: now().isoformat())
    
    # Versioning
    supersedes: Optional[str] = None  # Points to previous version
    
    # Knowledge
    entities: List[str] = field(default_factory=list)  # ["Python", ...]
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    pinned: bool = False  # Always inject
    hidden: bool = False  # Store but don't inject
```

---

## Detailed Feature Implementation

### Feature: Search

**User Command:**
```bash
memora search "how do I use async in Python?"
```

**Execution Flow:**

```python
def search(query: str, limit: int = 20) -> List[Memory]:
    # 1. Tokenize query
    tokens = tokenize(query)  # ["how", "use", "async", "python"]
    
    # 2. Query word index
    results_by_token = {}
    for token in tokens:
        results_by_token[token] = word_index.get(token, [])
    
    # 3. Find intersection (memories matching most tokens)
    candidate_ids = set(results_by_token[tokens[0]])
    for token in tokens[1:]:
        candidate_ids &= set(results_by_token.get(token, []))
    
    # 4. Score with BM25
    scores = {}
    for mem_id in candidate_ids:
        scores[mem_id] = bm25(
            query=tokens,
            memory_id=mem_id,
            total_memories=len(all_memories)
        )
    
    # 5. Sort and limit
    top_ids = sorted(scores, key=scores.get, reverse=True)[:limit]
    
    # 6. Load memories
    results = [store.read(mem_id) for mem_id in top_ids]
    
    return results
```

**Response:**
```
Found 5 memories matching "how do I use async in Python?"

1. async/await in Python (confidence: 0.98)
   Source: OLLAMA_CHAT | Session: sess_abc123
   Created: 2024-01-15 14:32:00
   Content: "Async programming in Python uses asyncio library..."

2. asyncio tutorial (confidence: 0.95)
   Source: FILE_INGESTION | Document
   ...
```

### Feature: Temporal Search

**User Command:**
```bash
memora when "last week"
```

**Execution Flow:**

```python
def search_by_time(time_query: str) -> List[Memory]:
    # 1. Parse time query
    start_date, end_date = parse_time_query(time_query)
    # "last week" → (today - 7 days, today)
    
    # 2. Find all memories in date range
    memories = []
    for date in generate_date_range(start_date, end_date):
        date_str = date.isoformat()
        if date_str in temporal_index:
            memories.extend(temporal_index[date_str])
    
    # 3. Load memories
    results = [store.read(mem_id) for mem_id in memories]
    
    # 4. Sort by date descending
    results = sorted(results, key=lambda m: m.created_at, reverse=True)
    
    return results
```

---

## Storage & Indexing

### Object Store Layout

```
.memora/
├── objects/                          # Git-like content store
│   ├── 1a/
│   │   ├── 2b3c4d5e6f7g8h9i0j.zlib  # ~1KB compressed
│   │   └── ...
│   ├── 2b/
│   │   └── ...
│   └── (256 directories, one per hex byte)
│
├── refs/
│   ├── heads/
│   │   ├── main                      # Current commit on main
│   │   ├── feature/python
│   │   └── ...
│   └── archive/
│       └── old_branch
│
├── sessions/
│   ├── active/
│   │   ├── sess_abc123.json          # Active session data
│   │   └── ...
│   └── closed/
│       ├── sess_def456.json
│       └── ...
│
├── graph/
│   ├── nodes.json                    # Entity nodes
│   └── edges.json                    # Relationships
│
├── index/
│   ├── words.json                    # word → [mem_ids]
│   ├── temporal.json                 # date → [mem_ids]
│   ├── sessions.json                 # session_id → [mem_ids]
│   └── types.json                    # type → [mem_ids]
│
├── branches/
│   ├── main.meta                     # Metadata
│   └── ...
│
└── config                            # Configuration
    ├── core
    │   └── version: "3.1"
    ├── storage
    │   └── compression: "zlib"
    ├── index
    │   └── enable_word_index: true
    └── sessions
        └── keep_closed_days: 30
```

---

## Algorithms & Performance

### Indexing Algorithm (Inverted Index)

```
Time Complexity:
- Adding memory to index: O(n) where n = words in memory
- Searching: O(k) where k = number of results
- Space: O(w * m) where w = unique words, m = memories per word

Typical Performance:
- Index 1KB of text: 1-5ms
- Search 1,000,000 memories: 5-50ms
- Combined index write + search: <100ms
```

### Deduplication Algorithm

```
Content Hash:
1. Serialize memory to JSON
2. Hash with SHA-256
3. Check if hash exists
4. If yes: skip (already have)
5. If no: store

Deduplication Rate:
- Typical: 10-30% of memories are duplicates
- Same conversation repeated: 100% duplicate
- Similar conversations: Fuzzy matching (future)

Storage Savings:
- Per-memory average: 1-2KB
- With deduplication: 0.7-1.5KB
- With compression: 0.3-0.8KB
```

### Search Ranking (BM25)

```
BM25 Formula:
score(doc) = sum( IDF(term) * (f(term) * (k1 + 1)) / (f(term) + k1 * (1 - b + b * |doc| / avgdoclen)) )

Where:
- IDF(term) = log((N - n(term) + 0.5) / (n(term) + 0.5))
- f(term) = term frequency in document
- |doc| = document length
- avgdoclen = average document length
- k1, b = parameters (typically 1.5, 0.75)

Result:
- Common terms weighted less
- Rare terms weighted more
- Document length normalized
- Top results most relevant
```

---

## Integration Points

### Ollama Integration

```
┌─ Client (user's LLM app)
│  └─ Connect to localhost:11435 (Memora proxy)
│     └─ Memora receives request
│        └─ Forward to localhost:11434 (Real Ollama)
│           └─ Ollama processes
│              └─ Return response
│                 └─ Memora intercepts response
│                    └─ Extract and queue for ingestion
│                       └─ Return response to client
│                          └─ Client sees normal Ollama response
│
│ Meanwhile:
│ Ingestion Pipeline (async) processes captured content
└─ Memory stored and indexed
```

### File Integration

```
User runs: memora ingest *.py

├─ Find all .py files
├─ For each file:
│  ├─ Detect type (file extension, content)
│  ├─ Extract content
│  ├─ Process through ingestion pipeline
│  ├─ Store memory
│  └─ Update indices
└─ Done
```

---

## Error Handling & Resilience

### Fallback Mechanisms

```python
def search_with_fallbacks(query: str) -> List[Memory]:
    try:
        # Try word index first (fastest)
        return word_index_search(query)
    except WordIndexCorruptedError:
        logger.warning("Word index corrupted, rebuilding...")
        rebuild_word_index()
        return word_index_search(query)
    except Exception as e:
        logger.error(f"Search failed: {e}, trying fallback...")
        # Fallback to sequential scan
        return sequential_search(query)

def ingest_with_resilience(content: str) -> Memory:
    try:
        return ingest(content)
    except NLPError:
        logger.warning("NLP failed, using keyword extraction...")
        return ingest_without_nlp(content)
    except CompressionError:
        logger.warning("Compression failed, storing uncompressed...")
        return store_uncompressed(content)
    except DiskFullError:
        logger.error("Disk full, cannot store")
        raise
```

---

## Scalability & Limits

### System Limits

```
Memory Count:
- Per branch: 100,000+
- Total: 1,000,000+
- Practical limit: Hardware dependent

Storage:
- Per memory: 100 bytes - 1MB (typical 1KB)
- Compression: 50% reduction
- Per 1,000,000 memories: ~500MB - 2GB

Index Size:
- Word index: ~100KB per 10,000 memories
- Temporal index: ~10KB per year
- Total index overhead: ~20-30% of storage

Performance:
- Search latency: <100ms for 1,000,000 memories
- Ingest latency: ~10-50ms per memory
- Branch operations: O(1) constant time
- Commit operations: O(1) constant time
```

### Scalability Considerations

```
For 1,000,000 memories:
1. Index size: ~100MB
2. Object store: ~500MB-2GB
3. Search latency: <100ms
4. Memory per instance: <500MB
5. Concurrent users: 10+

Optimization Strategies:
1. Lazy loading: Load indices on demand
2. Caching: LRU cache for hot objects
3. Batching: Batch index updates
4. Partitioning: Shard by branch (future)
5. Compression: zlib compression (enabled)
```

---

## Advanced Topics

### Conflict Resolution

```python
class ConflictDetector:
    def detect_conflict(self, mem1: Memory, mem2: Memory) -> Conflict:
        if self.temporal_supersession(mem1, mem2):
            return Conflict(
                type=ConflictType.TEMPORAL_SUPERSESSION,
                newer=mem2,
                older=mem1,
                status=ConflictStatus.AUTO_RESOLVED
            )
        
        if self.source_conflict(mem1, mem2):
            return Conflict(
                type=ConflictType.SOURCE_CONFLICT,
                memories=[mem1, mem2],
                status=ConflictStatus.UNRESOLVED
            )
        
        if self.direct_contradiction(mem1, mem2):
            return Conflict(
                type=ConflictType.DIRECT_CONTRADICTION,
                memories=[mem1, mem2],
                status=ConflictStatus.UNRESOLVED
            )
        
        return None
```

### Security & Privacy

```
PII Detection:
├─ Email addresses (regex + NER)
├─ Phone numbers (pattern matching)
├─ Credit card numbers (Luhn algorithm)
├─ SSN (pattern matching)
└─ API keys (entropy detection)

Action on Detection:
├─ Mask: Replace with [PII_EMAIL], [PII_PHONE]
├─ Remove: Delete entirely
├─ Warn: Alert user
└─ Log: Track what was filtered

Local Storage:
├─ No cloud uploads
├─ No telemetry
├─ User controls all data
├─ Encryption optional (future)
```

---

## Summary

Memora is a **5-layer system** designed for:

1. **Transparency**: Human-readable storage, Git-like versioning
2. **Scalability**: 1M+ memories, sub-100ms search
3. **Reliability**: ACID-like guarantees, automatic recovery
4. **Privacy**: Local-first, no external dependencies
5. **Extensibility**: Plugin architecture, REST API

Each layer handles one concern:
- **Layer 1**: Data models (what we store)
- **Layer 2**: Integration (how external systems connect)
- **Layer 3**: Storage (where things go)
- **Layer 4**: Logic (how things work)
- **Layer 5**: Interface (how users interact)

Every feature has fallbacks, and every operation is resilient to failures.
