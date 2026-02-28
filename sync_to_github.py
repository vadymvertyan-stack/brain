#!/usr/bin/env python3
"""
Second Brain Sync Script
========================
Automates note-taking using Zettelkasten method with PARA organization.
Takes conversation text as input, creates atomic notes, and syncs to GitHub.

Usage:
    python sync_to_github.py --input "conversation text here"
    python sync_to_github.py --file input.txt
    python sync_to_github.py --interactive
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Configuration
GITHUB_REPO = "vadymvertyan-stack/brain-second-brain"
SSH_KEY_PATH = "/root/.ssh/brain_github"
GIT_USER_NAME = "Kilo Code"
GIT_USER_EMAIL = "kilocode@secondbrain.local"

# PARA Structure
PARA_CATEGORIES = {
    "projects": "100-projects",
    "areas": "200-areas",
    "resources": "300-resources",
    "archives": "400-archives",
    "evergreens": "500-evergreens",
}

# Default category
DEFAULT_CATEGORY = "evergreens"


def generate_unique_id(content: str, timestamp: str) -> str:
    """Generate a unique Zettelkasten ID based on content hash."""
    hash_input = f"{timestamp}-{content[:100]}"
    hash_obj = hashlib.md5(hash_input.encode())
    short_hash = hash_obj.hexdigest()[:6]
    return f"note-{short_hash}"


def generate_note_id() -> str:
    """Generate a timestamp-based note ID."""
    return datetime.now().strftime("%Y%m%d%H%M") + "-"


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Second Brain Sync - Zettelkasten Note Taking System"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Conversation text to convert into a note"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to file containing conversation text"
    )
    parser.add_argument(
        "--interactive", "-int",
        action="store_true",
        help="Interactive mode for inputting notes"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=list(PARA_CATEGORIES.keys()),
        default=DEFAULT_CATEGORY,
        help=f"PARA category for the note (default: {DEFAULT_CATEGORY})"
    )
    parser.add_argument(
        "--title", "-t",
        type=str,
        help="Title for the note (auto-detected if not provided)"
    )
    parser.add_argument(
        "--tags", "-tag",
        type=str,
        help="Comma-separated tags for the note"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview note without saving or syncing"
    )
    return parser.parse_args()


def get_interactive_input() -> str:
    """Get note content from interactive input."""
    print("\n" + "=" * 50)
    print("Second Brain - Note Creation")
    print("=" * 50)
    print("Enter your note content (press Ctrl+D or type END on a new line to finish):\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    
    return "\n".join(lines)


def detect_category(content: str) -> str:
    """Detect the appropriate PARA category based on content analysis."""
    content_lower = content.lower()
    
    # Projects - active work with clear deliverables
    project_keywords = ["project", "implement", "build", "create", "develop", "task", "deadline", "milestone"]
    if any(kw in content_lower for kw in project_keywords):
        if "active" in content_lower or "working on" in content_lower:
            return "projects"
    
    # Areas - ongoing responsibilities
    area_keywords = ["responsibility", "area", "manage", "oversee", "maintain", "support"]
    if any(kw in content_lower for kw in area_keywords):
        return "areas"
    
    # Resources - learning and reference material
    resource_keywords = ["learn", "study", "reference", "tutorial", "documentation", "research", "book", "course"]
    if any(kw in content_lower for kw in resource_keywords):
        return "resources"
    
    # Archives - completed or inactive
    archive_keywords = ["completed", "finished", "archived", "inactive", "old", "deprecated"]
    if any(kw in content_lower for kw in archive_keywords):
        return "archives"
    
    # Evergreens - permanent, reusable knowledge
    return "evergreens"


def extract_title(content: str) -> str:
    """Extract or generate a title from the content."""
    lines = content.strip().split("\n")
    
    # First non-empty line might be a title
    for line in lines:
        clean_line = line.strip()
        if clean_line and len(clean_line) > 3:
            # Remove common prefixes
            clean_line = re.sub(r'^(notes?|notes on|note:|conversation:|discussion:)\s*', '', clean_line, flags=re.IGNORECASE)
            if clean_line:
                # Capitalize properly
                return clean_line.title()
    
    # Generate title from first few words
    words = content.split()[:5]
    return " ".join(words).title() + "..." if len(words) >= 5 else " ".join(words).title()


def extract_tags(content: str) -> list[str]:
    """Extract tags from content using common patterns."""
    tags = set()
    
    # Extract hashtags
    hashtags = re.findall(r'#(\w+)', content)
    tags.update(hashtags)
    
    # Extract keywords that might be tags
    important_words = re.findall(r'\b([A-Z][a-z]+(?:\+[A-Z][a-z]+)*)\b', content)
    for word in important_words:
        if len(word) > 3 and word not in ["This", "That", "The", "These", "Those", "Brain", "Second"]:
            tags.add(word.lower())
    
    # Limit to 5 tags
    return list(tags)[:5]


def parse_links(content: str) -> list[str]:
    """Parse wiki-style links from content."""
    # Look for [[note-id]] or [[note title]] patterns
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    return links


def create_note_content(
    note_id: str,
    title: str,
    content: str,
    category: str,
    tags: list[str],
    links: list[str]
) -> str:
    """Create a complete note with frontmatter and content."""
    
    # Build frontmatter
    frontmatter = f"""---
id: {note_id}
title: {title}
tags: [{', '.join(tags)}]
date: {datetime.now().strftime('%Y-%m-%d')}
category: {category}
links: [{', '.join([f'[[{link}]]' for link in links])}]
---

# {title}

"""
    
    # Process content into sections using CODE method
    processed_content = process_content_code_method(content)
    
    return frontmatter + processed_content


def process_content_code_method(content: str) -> str:
    """Process content using the CODE method: Capture, Organize, Distill, Express."""
    
    lines = content.strip().split("\n")
    
    # Separate into sections
    capture_section = []
    organize_section = []
    distill_section = []
    express_section = []
    
    current_section = "capture"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line_lower = line.lower()
        
        # Detect section markers
        if any(marker in line_lower for marker in ["detail", "detail:", "details:", "content:"]) and len(line) < 20:
            current_section = "organize"
            continue
        if any(marker in line_lower for marker in ["summary:", "conclusion:", "key point:"]) and len(line) < 20:
            current_section = "distill"
            continue
        if any(marker in line_lower for marker in ["action:", "next step:", "result:", "connection:"]) and len(line) < 20:
            current_section = "express"
            continue
        
        # Add line to current section
        if current_section == "capture":
            capture_section.append(line)
        elif current_section == "organize":
            organize_section.append(line)
        elif current_section == "distill":
            distill_section.append(line)
        else:
            express_section.append(line)
    
    # Build processed content
    result = []
    
    if capture_section:
        result.append("## Capture\n")
        result.append(" ".join(capture_section))
        result.append("\n")
    
    if organize_section:
        result.append("## Organize\n")
        result.append(" ".join(organize_section))
        result.append("\n")
    
    if distill_section:
        result.append("## Distill\n")
        result.append(" ".join(distill_section))
        result.append("\n")
    
    if express_section:
        result.append("## Express\n")
        result.append(" ".join(express_section))
        result.append("\n")
    
    # If no clear sections, create default structure
    if not result:
        result.append("## Summary\n")
        result.append(content[:200])
        if len(content) > 200:
            result.append("...\n")
        
        result.append("\n## Details\n")
        result.append(content[200:])
    
    return "\n".join(result)


def setup_git_repo(base_path: Path) -> None:
    """Initialize git repository if not already initialized."""
    git_dir = base_path / ".git"
    
    if not git_dir.exists():
        print("Initializing git repository...")
        subprocess.run(
            ["git", "init"],
            cwd=base_path,
            check=True,
            capture_output=True
        )
        
        # Configure git user
        subprocess.run(
            ["git", "config", "user.name", GIT_USER_NAME],
            cwd=base_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", GIT_USER_EMAIL],
            cwd=base_path,
            check=True,
            capture_output=True
        )
        
        # Add remote
        remote_url = f"git@github.com:KiloCode/{GITHUB_REPO}.git"
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=base_path,
            check=True,
            capture_output=True
        )
        
        print("Git repository initialized.")
    else:
        print("Git repository already exists.")


def sync_to_github(base_path: Path, note_filename: str) -> bool:
    """Commit and push changes to GitHub."""
    print("\nSyncing to GitHub...")
    
    try:
        # Add the new note
        subprocess.run(
            ["git", "add", note_filename],
            cwd=base_path,
            check=True,
            capture_output=True
        )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=base_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            print("No changes to commit.")
            return True
        
        # Commit with timestamp
        commit_message = f"Add note: {note_filename} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=base_path,
            check=True,
            capture_output=True
        )
        
        print(f"Committed: {commit_message}")
        
        # Set up SSH command for git
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no"
        
        # Push to GitHub
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=base_path,
            check=True,
            capture_output=True,
            env=env
        )
        
        print("Successfully pushed to GitHub!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        print(f"stderr: {e.stderr.decode() if e.stderr else 'No error output'}")
        return False


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Get content from appropriate source
    content = ""
    
    if args.interactive:
        content = get_interactive_input()
    elif args.input:
        content = args.input
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        print("Error: No input provided. Use --input, --file, or --interactive")
        sys.exit(1)
    
    if not content.strip():
        print("Error: Empty content provided")
        sys.exit(1)
    
    # Determine category
    category = args.category if args.category != DEFAULT_CATEGORY else detect_category(content)
    category_folder = PARA_CATEGORIES[category]
    
    # Extract metadata
    title = args.title if args.title else extract_title(content)
    tags = args.tags.split(",") if args.tags else extract_tags(content)
    links = parse_links(content)
    
    # Generate IDs
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = generate_unique_id(content, timestamp)
    note_id = generate_note_id() + unique_id
    
    # Create note filename
    filename = f"{note_id}.md"
    
    # Create note content
    note_content = create_note_content(
        note_id=note_id,
        title=title,
        content=content,
        category=category_folder,
        tags=tags,
        links=links
    )
    
    if args.dry_run:
        print("\n" + "=" * 50)
        print("DRY RUN - Note Preview")
        print("=" * 50)
        print(f"Category: {category_folder}")
        print(f"Filename: {filename}")
        print(f"Title: {title}")
        print(f"Tags: {tags}")
        print(f"Links: {links}")
        print("\n" + "-" * 50)
        print("Content:")
        print("-" * 50)
        print(note_content)
        print("=" * 50)
        return
    
    # Determine base path
    base_path = Path("/root/brain-second-brain")
    
    # Create directory structure
    category_path = base_path / category_folder
    category_path.mkdir(parents=True, exist_ok=True)
    
    # Create note file
    note_path = category_path / filename
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(note_content)
    
    print(f"\nNote created: {note_path}")
    print(f"Category: {category_folder}")
    print(f"Title: {title}")
    print(f"Tags: {tags}")
    
    # Setup git and sync
    setup_git_repo(base_path)
    sync_to_github(base_path, f"{category_folder}/{filename}")
    
    print("\n✓ Second brain sync complete!")


if __name__ == "__main__":
    main()
