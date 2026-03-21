import os
import subprocess

def run_command(command, env=None):
    try:
        subprocess.run(command, check=True, shell=True, env=env)
    except subprocess.CalledProcessError as e:
        if "git commit" in command:
            print("Nothing to commit for this stage.")
        else:
            print(f"Error: {command}\n{e}")

stages = [
    {
        "date": "2026-03-19T10:00:00",
        "message": "Initialize project scaffold with Poetry and shared data models",
        "add": [
            "pyproject.toml",
            "poetry.lock",
            "README.md",
            ".gitignore",
            ".env.example",
            "src/memora/__init__.py",
            "src/memora/shared/",
        ],
    },
    {
        "date": "2026-03-20T14:00:00",
        "message": "feat: add core storage engine — CAS objects, indexes, ingestion, and conflict detection",
        "add": [
            "src/memora/core/",
            "tests/",
        ],
    },
    {
        "date": "2026-03-21T11:00:00",
        "message": "feat: add public API, CLI, proxy server, and frontend chat interface",
        "add": [
            ".",
        ],
    },
]

env = os.environ.copy()

for stage in stages:
    print(f"\n--- Committing: {stage['message']} ---")
    for path in stage["add"]:
        if path == "." or os.path.exists(path):
            run_command(f'git add "{path}"')
        else:
            print(f"Skipping: {path} not found")
    env["GIT_AUTHOR_DATE"] = stage["date"]
    env["GIT_COMMITTER_DATE"] = stage["date"]
    run_command(f'git commit -m "{stage["message"]}"', env=env)

print("\nDone. Run: git log --oneline")