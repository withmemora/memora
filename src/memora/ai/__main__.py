"""Entry point for running Memora AI modules."""

import os
import sys

# Get configuration from environment
proxy_port = int(os.getenv("MEMORA_PROXY_PORT", "11435"))
ollama_host = os.getenv("MEMORA_OLLAMA_HOST", "http://localhost:11434")
memory_path = os.getenv("MEMORA_MEMORY_PATH", "./memora_data")
verbose = os.getenv("MEMORA_VERBOSE", "true").lower() == "true"

# Run proxy
from memora.ai.ollama_proxy import start_proxy

if __name__ == "__main__":
    start_proxy(
        ollama_host=ollama_host,
        proxy_port=proxy_port,
        memory_path=memory_path,
        verbose=verbose,
    )
