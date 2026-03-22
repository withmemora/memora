# Phase 0-3 Implementation Plan

## 🎯 Goal
Build the **core storage foundation** (Phases 0-3) to enable parallel development:
- **You:** Phases 0-3 (storage core) → then docs/website/branding
- **Teammate:** Phases 4-13 (business logic, APIs, UIs) using your foundation

---

## ✅ Phase 0: COMPLETED (100%)

**Status:** ✅ **DONE** - All files implemented, tested, and committed

### What Was Built:
- ✅ `shared/models.py` - All data classes (Fact, MemoryCommit, Conflict, etc.)
- ✅ `shared/interfaces.py` - Complete CoreEngineInterface contract (57 methods)
- ✅ `shared/exceptions.py` - All 8 custom exceptions
- ✅ Complete test suite (680+ lines for models, 170+ for exceptions)
- ✅ CI/CD pipeline configured and passing
- ✅ Coverage at 100% (interfaces excluded from calculation)

### Verification:
```bash
pytest tests/shared/ -v  # All 60 tests passing
poetry run ruff check src/  # No linting errors
```

**Commits:**
- `291d5bf` - fix: resolve CI failures with comprehensive test suite
- `87f06ee` - fix: remove unused imports to resolve ruff linting errors
- `2957540` - fix: exclude abstract interfaces from coverage calculation

---

## 📦 Phase 1: Object Serialization (TODO)

**Status:** ❌ **NEXT TO IMPLEMENT**

**Estimated Time:** 6-8 hours

**File:** `src/memora/core/objects.py`

### What It Does:
Implements the complete serialization protocol for all Memora objects:
1. Object → dict → sorted JSON → UTF-8 bytes → zlib compress → SHA-256 hash
2. Reverse: compressed bytes → decompress → JSON → dict → object

### Functions to Implement:
```python
# Hashing
def hash_bytes(data: bytes) -> str
def hash_object(obj_dict: dict) -> str
def hash_fact(fact: Fact) -> str  # Only content_type+entity+attribute+value

# Serialization (returns tuple of compressed bytes + hash)
def serialize_fact(fact: Fact) -> tuple[bytes, str]
def serialize_tree(tree: MemoryTree) -> tuple[bytes, str]
def serialize_commit(commit: MemoryCommit) -> tuple[bytes, str]

# Deserialization
def deserialize_fact(data: bytes) -> Fact
def deserialize_tree(data: bytes) -> MemoryTree
def deserialize_commit(data: bytes) -> MemoryCommit

# Verification
def verify_hash(data: bytes, expected: str) -> None  # raises HashMismatchError
```

### Critical Requirements:
- ✅ Use `json.dumps(d, separators=(',',':'), sort_keys=True)` - **sort_keys is MANDATORY**
- ✅ Use `zlib.compress(data, level=6)` - **NOT gzip**
- ✅ Fact hash excludes: content, source, observed_at, confidence
- ✅ All entity and attribute names must be lowercased in hash computation

### Tests to Write: `tests/core/test_objects.py`
- Round-trip: serialize → deserialize returns identical object
- Hash determinism: same fact 100 times = same hash
- Deduplication: changing source/confidence doesn't change hash
- Sort keys: `{b:1,a:2}` and `{a:2,b:1}` produce same hash
- Corruption: verify_hash raises HashMismatchError on tampered data
- Target coverage: 95%+

### Verification Checklist:
- [ ] Same fact content 100 times = same hash every time
- [ ] Changing source/timestamp/confidence does NOT change fact hash
- [ ] Objects are zlib-compressed (cannot cat them as plain text)
- [ ] verify_hash raises HashMismatchError on corrupted bytes
- [ ] pytest tests/core/test_objects.py — all pass, coverage ≥ 95%

### Phase 1 Prompt:
```
Implement src/memora/core/objects.py completely.

Read .arc/CLAUDE.md serialization protocol section before writing.

SERIALIZATION PROTOCOL — exact order, no deviations:
  1. to_dict() on object → Python dict
  2. json.dumps(d, separators=(',',':'), sort_keys=True)
  3. Encode to UTF-8 bytes
  4. zlib.compress(data, level=6)  — NOT gzip
  5. hashlib.sha256(compressed).hexdigest()

[Copy functions list from above]

Add to_dict() and from_dict() to shared/models.py if not present.

Write tests/core/test_objects.py covering all test cases above.
Coverage target: 95%+
```

---

## 🗄️ Phase 2: Object Store + Refs (TODO)

**Status:** ❌ **AFTER PHASE 1**

**Estimated Time:** 8-10 hours

**Files:** `src/memora/core/store.py`, `src/memora/core/refs.py`

### What It Does:
Implements Git-style content-addressable storage:
- Write objects to disk at `objects/{hash[:2]}/{hash[2:]}`
- Atomic writes (tmp file → os.replace)
- File locking to prevent concurrent corruption
- Branch pointer and HEAD management
- `memora init` directory structure creation

### Key Classes/Functions:

**store.py:**
```python
class ObjectStore:
    def write(self, obj: Fact|MemoryTree|MemoryCommit) -> str
    def read_fact(self, hash: str) -> Fact
    def read_tree(self, hash: str) -> MemoryTree
    def read_commit(self, hash: str) -> MemoryCommit
    def exists(self, hash: str) -> bool
    def acquire_lock(self)  # filelock, 30s timeout
    def release_lock(self)
    def list_all_hashes(self) -> list[str]
    
    @staticmethod
    def initialize_directories(store_path: Path)
```

**refs.py:**
```python
def get_branch(store_path, name) -> str
def set_branch(store_path, name, hash)
def get_head(store_path) -> tuple[str|None, str|None]
def set_head_to_branch(store_path, name)
def list_branches(store_path) -> list[tuple[str,str]]
```

### .memora/ Directory Structure:
```
.memora/
    objects/
        {aa}/
            {62-char-hash}
        tmp/
    refs/
        heads/
            main
    HEAD                          # "ref: refs/heads/main"
    staging/
        STAGE                     # JSON: ["hash1", "hash2"]
    conflicts/
        open/
        resolved/
    index/
        entities.json
        topics.json
        temporal.json
    config                        # JSON: {auto_commit:true, ...}
    .write_lock
```

### Critical Requirements:
- ✅ Atomic writes: always write to `.tmp` file first, then `os.replace(tmp, final)`
- ✅ Deduplication: if hash exists, skip write (return existing hash)
- ✅ File locking: use `filelock.FileLock` with 30s timeout
- ✅ Set permissions to 0o700 on non-Windows (privacy)
- ✅ Hash verification on every read

### Tests to Write: `tests/core/test_store.py`
- Write then read returns identical data
- Write same object twice creates only ONE file (deduplication)
- ObjectNotFoundError for missing hash
- HashMismatchError when file manually corrupted
- Lock acquisition and release
- initialize_directories creates correct structure
- Atomic writes succeed even with concurrent access

### Verification Checklist:
- [ ] memora init creates .memora/ with all subdirectories
- [ ] HEAD file contains 'ref: refs/heads/main'
- [ ] Write a Fact, read it back — identical data
- [ ] Write same Fact twice — only ONE file in objects/
- [ ] Corrupt a stored file — reading raises HashMismatchError
- [ ] pytest tests/core/test_store.py — all pass

---

## 📋 Phase 3: Staging + Indexes (TODO)

**Status:** ❌ **AFTER PHASE 2**

**Estimated Time:** 6-8 hours

**Files:** `src/memora/core/staging.py`, `src/memora/core/index.py`

### What It Does:
Implements staging area (like `git add`) and three derived indexes for fast retrieval.

### staging.py Functions:
```python
def add_to_staging(store_path, fact_hash)
def get_staged_hashes(store_path) -> list[str]
def get_staged_facts(store_path, store) -> list[tuple[str,Fact]]
def clear_staging(store_path)
def staging_is_empty(store_path) -> bool
def staging_count(store_path) -> int
```

### index.py Class:
```python
class IndexLayer:
    def update_indexes(self, new_facts: list[tuple[str,Fact]])
    def get_by_entity(self, name: str) -> list[str]
    def get_by_topic(self, path: str, prefix=False) -> list[str]
    def get_by_time_range(self, start, end) -> list[tuple[str,str]]
    def entity_exists(self, name: str) -> bool
    def rebuild_indexes(self, store: ObjectStore)  # CRITICAL!
```

### Three Index Files:

**1. entities.json**
```json
{
  "user": ["hash1", "hash2"],
  "current_project": ["hash3"]
}
```

**2. topics.json**
```json
{
  "personal": ["hash1"],
  "personal/name": ["hash1"],
  "projects": ["hash2", "hash3"],
  "projects/memora": ["hash2"],
  "projects/memora/deadline": ["hash3"]
}
```

**3. temporal.json**
```json
[
  ["2026-01-15T10:30:00Z", "hash1", "user"],
  ["2026-01-15T11:45:00Z", "hash2", "current_project"]
]
```

### Critical Requirements:
- ✅ Entity index: all entity names lowercase
- ✅ Topic index: hierarchical — child path adds to all parent paths
- ✅ Temporal index: **always sorted ascending** by timestamp (use `bisect.insort`)
- ✅ **REBUILD GUARANTEE**: `rebuild_indexes()` must produce IDENTICAL result to incremental build
- ✅ All staging writes atomic (tmp → os.replace)

### Tests to Write: `tests/core/test_index.py`
- Entity lookup returns correct hashes
- Topic hierarchy: 'projects/x/deadline' adds to 'projects/x' and 'projects'
- Temporal index remains sorted after inserts
- **REBUILD GUARANTEE**: destroy indexes, rebuild, compare = identical
- Staging add/clear/count operations
- Empty staging returns [] without errors

### Verification Checklist:
- [ ] STAGE file starts as '[]' after init
- [ ] Adding fact to stage updates STAGE correctly
- [ ] Entity index lookup returns correct fact hashes
- [ ] Temporal index sorted ascending after multiple inserts
- [ ] Topic hierarchy works correctly (test with 'a/b/c' paths)
- [ ] **REBUILD GUARANTEE PASSES** (most critical test)
- [ ] pytest tests/core/test_index.py — all pass

---

## 🤝 Handoff Point After Phase 3

### What Your Teammate Gets:

✅ **Complete Storage System:**
- Object serialization with SHA-256 hashing
- Content-addressable storage (Git-style)
- Branch and HEAD management
- Staging area (facts waiting to commit)
- Three indexes for fast retrieval
- 95%+ test coverage on all components

✅ **What Works:**
```python
# Your teammate can do this:
from memora.core.store import ObjectStore
from memora.core.staging import add_to_staging
from memora.core.index import IndexLayer
from memora.shared.models import Fact

# Initialize store
ObjectStore.initialize_directories(Path(".memora"))
store = ObjectStore(Path(".memora"))

# Create and store a fact
fact = Fact(
    content="My name is Alice",
    content_type=ContentType.TRIPLE,
    entity="user",
    attribute="name",
    value="Alice",
    source="test",
    observed_at=datetime.now(),
    confidence=0.95
)

fact_hash = store.write(fact)  # Returns SHA-256 hash
add_to_staging(Path(".memora"), fact_hash)

# Retrieve it
retrieved = store.read_fact(fact_hash)
assert retrieved.value == "Alice"
```

### What They Build Next:

**Phase 4:** Atomic commit operation
- Uses your `store.write()` to persist commits
- Uses your `staging.py` to get facts to commit
- Uses your `index.update_indexes()` after commit

**Phase 5:** NLP ingestion pipeline
- Uses your `serialize_fact()` to compute hashes
- Uses your `store.exists()` for deduplication
- Uses your `staging.add_to_staging()` to stage extracted facts

**Phase 6:** Conflict detection
- Uses your `index.get_by_entity()` to find existing facts
- Uses your `store.write()` to persist conflicts

**Phases 7-13:** All higher layers
- Use your complete storage foundation

---

## 📝 What You Build in Parallel

While your teammate works on Phases 4-13, you'll build:

### Documentation (Phase 14):
- MkDocs site with Material theme
- Architecture guide (explain the 3-layer design)
- API reference (auto-generated from docstrings)
- Tutorial: "Building a Memory-Enabled Chatbot"
- Conflict resolution guide

### Landing Page (Phase 15):
- Single-page HTML
- Hero: "Git-Style Versioned Memory for Any LLM"
- 3 USPs: Conflict Detection, Version History, Local-First
- Demo video embed
- Quick start guide
- GitHub star button

### README + Assets (Phase 16):
- Compelling README.md with demo GIF
- Architecture diagram (show 3 layers)
- Installation instructions
- Quick start example
- Links to docs

### Branding:
- Logo files (SVG + PNG)
- Design system documentation
- Color palette reference
- Typography guide

---

## 📊 Timeline Estimate

| Phase | Your Work | Teammate's Work | Parallel Work |
|-------|-----------|-----------------|---------------|
| **0** | ✅ Done | - | - |
| **1** | 6-8h | Wait | - |
| **2** | 8-10h | Wait | - |
| **3** | 6-8h | Wait | - |
| **Handoff** | - | - | - |
| **4-6** | - | 24-36h | Docs setup, outline |
| **7-10** | - | 24-32h | Write docs, landing page |
| **11-13** | - | 22-28h | README, assets, polish |

**Total:** 
- Your work: 20-26h (Phases 1-3) + 30-40h (docs/website) = **50-66 hours**
- Teammate: 70-96h (Phases 4-13)
- **Parallel time saved:** ~40-50 hours

---

## 🚀 Next Steps

1. **Start Phase 1 now:**
   ```bash
   # Copy Phase 1 prompt from above
   # Implement core/objects.py
   # Run: pytest tests/core/test_objects.py -v
   ```

2. **Verify Phase 1 checklist** - all items must pass

3. **Move to Phase 2** - implement store.py and refs.py

4. **Verify Phase 2 checklist** - test atomic writes and locking

5. **Complete Phase 3** - staging and indexes with rebuild guarantee

6. **Handoff to teammate** with complete storage foundation

7. **Start parallel work** on docs and website

---

## 📌 Remember

**Keep it simple:**
- Follow the exact function signatures from CLAUDE.md
- Copy the Phase prompts verbatim - they're battle-tested
- Run tests after every function
- Commit after every passing test suite
- Don't add features beyond the spec

**Communication:**
- Document any deviations in comments
- Write clear docstrings for every public function
- Keep test names descriptive
- Update this file if you change the plan

**You've got this!** Phase 0 is rock solid. Phases 1-3 are well-specified. Just follow the prompts.
