"""Configuration constants for Memora."""

# File processing limits
MAX_FILE_SIZE_MB = 50  # Maximum file size for ingestion
MAX_TEXT_LENGTH = 1_000_000  # Maximum characters for text processing
MAX_PDF_PAGES = 100  # Maximum PDF pages to process

# Memory limits
MAX_MEMORIES_PER_SESSION = 1000  # Safety limit for session memory count
MAX_CONTEXT_MEMORIES = 200  # Maximum memories to inject into LLM context
MAX_CONTEXT_TOKENS = 4000  # Approximate token limit for context injection

# Security settings
ENABLE_SENSITIVE_FILTER = True  # Enable content filtering by default
REDACTION_REPLACEMENT = "[REDACTED]"  # What to replace sensitive content with

# Graph settings
MAX_GRAPH_NODES = 10000  # Maximum nodes in knowledge graph
MAX_GRAPH_EDGES = 50000  # Maximum edges in knowledge graph

# Index settings
MAX_WORD_INDEX_TERMS = 100000  # Maximum terms in word index
MAX_INDEX_FILE_SIZE_MB = 10  # Maximum size for index files

# Branch settings
DEFAULT_SESSION_LIMIT = 100
DEFAULT_MEMORY_LIMIT = 5000
DEFAULT_TIME_LIMIT_DAYS = 90

# Ollama instance configuration
DEFAULT_OLLAMA_TARGETS = {
    "primary": {"host": "localhost", "port": 11434, "priority": 1},
}
MAX_OLLAMA_INSTANCES = 10

# Supported file extensions
SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".log"}
SUPPORTED_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".css",
    ".html",
    ".xml",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
ALL_SUPPORTED_EXTENSIONS = (
    SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_CODE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS
)

# Languages supported by code extractor
SUPPORTED_LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "java",
    "cpp",
    "c",
    "csharp",
    "go",
    "rust",
    "php",
    "ruby",
    "swift",
    "kotlin",
    "scala",
    "shell",
    "bash",
    "sql",
    "html",
    "css",
    "json",
    "xml",
    "yaml",
    "markdown",
    "dockerfile",
    "makefile",
}

# Graph relation types
GRAPH_RELATION_TYPES = {
    "works_at",
    "employed_by",
    "knows",
    "friend_of",
    "colleague_of",
    "works_with",
    "located_in",
    "based_in",
    "lives_in",
    "from",
    "building",
    "working_on",
    "developing",
    "creating",
    "considering",
    "evaluating",
    "uses",
    "prefers",
    "likes",
    "dislikes",
    "skilled_in",
    "learning",
    "related_to",
    "part_of",
    "owns",
    "manages",
    "leads",
    "reports_to",
    "member_of",
}
