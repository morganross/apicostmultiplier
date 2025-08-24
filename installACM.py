#!/usr/bin/env python3
"""
installACM.py

Installer/downloader for apicostmultiplier's external dependencies.

Behavior:
- Downloads the listed GitHub projects (either as zip archives or via git clone fallback).
- Each project is placed into its own child folder under this repository root.
- Adds each target folder to .gitignore in the repo root so downloaded code is not committed.
- Does NOT execute any installers or run code from downloaded projects. This script only downloads and extracts/clones.

Usage:
    python installACM.py          # performs downloads (default: use zip whenever possible)
    python installACM.py --dry   # show planned actions without downloading
    python installACM.py --clone # prefer git clone instead of zip archives (if git available)

Notes:
- For GitHub repo URLs, the script will try to download the default branch as a zip (tries 'main' then 'master').
  If zip download fails and --clone is specified (or zip fails and git is available), it will fall back to `git clone`.
- The script is conservative: it creates folders only when downloads succeed.
- The script appends folder entries to .gitignore (creates .gitignore if missing).
"""

import os
import sys
import argparse
import tempfile
import shutil
import zipfile
import subprocess
from urllib.parse import urlparse
try:
    import requests
except Exception:
    requests = None

ROOT = os.path.dirname(os.path.abspath(__file__))

# Downloads list requested by the user.
# Each entry: "name" is the target folder name (child of ROOT),
# "type" is "zip" for a direct zip URL, or "repo" for a GitHub repo URL (will try zip of default branch).
DOWNLOADS = [
    {
        "name": "gpt-researcher-v3.3.3",
        "type": "zip",
        "url": "https://github.com/assafelovic/gpt-researcher/archive/refs/tags/v.3.3.3.zip"
    },
    {
        "name": "gptr-eval-process",
        "type": "repo",
        "url": "https://github.com/morganross/gptr-eval-process"
    },
    {
        "name": "FilePromptForge",
        "type": "repo",
        "url": "https://github.com/morganross/FilePromptForge"
    },
    {
        "name": "llm-doc-eval",
        "type": "repo",
        "url": "https://github.com/morganross/llm-doc-eval"
    },
    {
        "name": "GPT-Researcher-Multi-Agent-CLI",
        "type": "repo",
        "url": "https://github.com/morganross/GPT-Researcher-Multi-Agent-CLI"
    },
]


def ensure_requests():
    global requests
    if requests is None:
        raise RuntimeError("The 'requests' library is required. Install with: pip install requests")


def safe_makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def write_gitignore_entries(entries):
    gitignore_path = os.path.join(ROOT, ".gitignore")
    existing = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing = f.read()
    existing_lines = set([line.rstrip() for line in existing.splitlines() if line.strip() != ""])
    to_append = []
    for e in entries:
        # normalize to posix style folder paths (no leading ./)
        line = e.rstrip("/\\") + "/"
        if line not in existing_lines:
            to_append.append(line)
    if to_append:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n# Downloaded by installACM.py\n")
            for line in to_append:
                f.write(line + "\n")
        print(f"Appended {len(to_append)} entries to .gitignore")
    else:
        print("No changes required to .gitignore")


def download_file_stream(url, dest_path):
    ensure_requests()
    print(f"Downloading: {url}")
    with requests.get(url, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def extract_zip_to_folder(zip_path, dest_folder):
    # Extract zip into a temporary folder then move content so dest_folder contains the project files (not an extra root dir).
    tmp_dir = tempfile.mkdtemp(prefix="acm_extract_")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tmp_dir)
        # Find the single root folder inside tmp_dir (common in GitHub zips) and move its contents.
        entries = [os.path.join(tmp_dir, e) for e in os.listdir(tmp_dir)]
        # If there's exactly one folder, move its contents; otherwise move all entries
        if len(entries) == 1 and os.path.isdir(entries[0]):
            src_root = entries[0]
            safe_makedirs(dest_folder)
            for item in os.listdir(src_root):
                s = os.path.join(src_root, item)
                d = os.path.join(dest_folder, item)
                if os.path.exists(d):
                    # avoid overwrite: remove existing, then move
                    if os.path.isdir(d):
                        shutil.rmtree(d)
                    else:
                        os.remove(d)
                shutil.move(s, d)
        else:
            safe_makedirs(dest_folder)
            for item in os.listdir(tmp_dir):
                s = os.path.join(tmp_dir, item)
                d = os.path.join(dest_folder, item)
                if os.path.exists(d):
                    if os.path.isdir(d):
                        shutil.rmtree(d)
                    else:
                        os.remove(d)
                shutil.move(s, d)
    finally:
        shutil.rmtree(tmp_dir)


def try_download_zip(url, dest_folder, dry=False):
    tmp_zip = None
    try:
        fd, tmp_zip = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        if dry:
            print(f"[DRY] Would download zip: {url} -> {dest_folder}")
            return True
        download_file_stream(url, tmp_zip)
        # create dest folder only after successful download+extract
        extract_zip_to_folder(tmp_zip, dest_folder)
        print(f"Extracted zip to {dest_folder}")
        return True
    except Exception as exc:
        print(f"Zip download/extract failed for {url}: {exc}")
        return False
    finally:
        if tmp_zip and os.path.exists(tmp_zip):
            try:
                os.remove(tmp_zip)
            except Exception:
                pass


def try_git_clone(repo_url, dest_folder, dry=False):
    if dry:
        print(f"[DRY] Would git clone: {repo_url} -> {dest_folder}")
        return True
    git = shutil.which("git")
    if not git:
        print("git not found in PATH; cannot clone.")
        return False
    try:
        cmd = [git, "clone", repo_url, dest_folder]
        print("Running:", " ".join(cmd))
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print("git clone failed:", e)
        return False


def repo_url_to_zip_candidates(repo_url):
    # Given https://github.com/owner/repo, produce candidate zip URLs to try.
    parsed = urlparse(repo_url)
    path = parsed.path.rstrip("/")
    if path.startswith("/"):
        path = path[1:]
    # candidate: refs/heads/main.zip then master
    candidates = [
        f"https://github.com/{path}/archive/refs/heads/main.zip",
        f"https://github.com/{path}/archive/refs/heads/master.zip",
    ]
    return candidates


def download_project(entry, prefer_clone=False, dry=False):
    name = entry["name"]
    typ = entry.get("type", "repo")
    url = entry["url"]
    dest_folder = os.path.join(ROOT, name)
    if os.path.exists(dest_folder) and os.listdir(dest_folder):
        print(f"Destination {dest_folder} already exists and is not empty. Skipping download.")
        return dest_folder  # still add to gitignore but skip
    if typ == "zip":
        success = try_download_zip(url, dest_folder, dry=dry)
        if not success and prefer_clone:
            # attempt to infer repo URL and git clone
            # try to convert zip url back to repo url (best-effort)
            parsed = urlparse(url)
            # naive conversion: remove '/archive/...' suffix
            repo_url = url
            for marker in ["/archive/refs/tags/", "/archive/refs/heads/"]:
                if marker in url:
                    repo_url = url.split(marker)[0]
                    break
            print(f"Falling back to git clone of {repo_url}")
            try_git_clone(repo_url, dest_folder, dry=dry)
    else:
        # type == repo: try zip of default branch first (main/master), then optionally git clone
        candidates = repo_url_to_zip_candidates(url)
        success = False
        for c in candidates:
            success = try_download_zip(c, dest_folder, dry=dry)
            if success:
                break
        if not success:
            if prefer_clone:
                print(f"Attempting git clone fallback for {url}")
                success = try_git_clone(url, dest_folder, dry=dry)
            else:
                print(f"Could not download {url} as zip and clone not requested.")
        if not success:
            print(f"Failed to obtain project {name} ({url}).")
    return dest_folder


def main():
    parser = argparse.ArgumentParser(description="Download external projects for apicostmultiplier")
    parser.add_argument("--dry", action="store_true", help="Show actions without performing downloads")
    parser.add_argument("--clone", action="store_true", help="Prefer git clone fallback when zip download fails")
    parser.add_argument("--target", type=str, default=None, help="Optional target folder (overrides internal names)")
    args = parser.parse_args()

    if args.dry:
        print("Running in dry mode. No changes will be made.")

    if args.dry and not requests:
        # in dry mode we don't need requests
        pass
    elif not requests:
        print("The 'requests' library is required for downloading. Install it with: pip install requests")
        sys.exit(1)

    created_dirs = []
    for entry in DOWNLOADS:
        # allow overriding name with --target for single-run quick tests
        dest = download_project(entry, prefer_clone=args.clone, dry=args.dry)
        if dest:
            created_dirs.append(os.path.basename(dest))

    # update .gitignore with these folder names
    if created_dirs:
        write_gitignore_entries(created_dirs)
    else:
        print("No directories created; .gitignore not modified.")

    print("Done.")


if __name__ == "__main__":
    main()
