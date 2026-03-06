#!/usr/bin/env python3
"""
Brain Auto-Sync Script
=====================
Automatically watches for changes in Brain directory and syncs to Git.
Can run as a scheduled task or continuous watcher.

Usage:
    python brain_autosync.py --watch    # Continuous watching
    python brain_autosync.py --schedule # Run on schedule (every 5 minutes)
    python brain_autosync.py --once     # Single sync
"""

import argparse
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Configuration
BRAIN_DIR = Path(r"e:\Vibe Code\Brain")
GIT_EXECUTABLE = "git"
MINIMUM_COMMIT_INTERVAL = 300  # seconds (5 minutes)
IGNORE_PATTERNS = [
    ".git/",
    "__pycache__/",
    "*.pyc",
    ".obsidian/",
    "*.tmp",
    ".cache/",
]


def get_changed_files() -> List[str]:
    """Get list of changed files in the repository."""
    try:
        result = subprocess.run(
            [GIT_EXECUTABLE, "status", "--porcelain"],
            cwd=BRAIN_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Get file path (skip status characters)
                file_path = line[3:].strip() if len(line) > 3 else line.strip()
                if file_path:
                    files.append(file_path)
        return files
    except Exception as e:
        print(f"Error getting changed files: {e}")
        return []


def should_ignore(file_path: str) -> bool:
    """Check if file should be ignored."""
    for pattern in IGNORE_PATTERNS:
        if pattern.endswith("/"):
            if pattern[:-1] in file_path.split("/"):
                return True
        elif pattern.startswith("*"):
            if file_path.endswith(pattern[1:]):
                return True
        else:
            if pattern in file_path:
                return True
    return False


def filter_changed_files(files: List[str]) -> List[str]:
    """Filter out ignored files."""
    return [f for f in files if not should_ignore(f)]


def get_last_sync_time() -> Optional[datetime]:
    """Get the time of the last sync from a marker file."""
    marker_file = BRAIN_DIR / ".last_sync"
    if marker_file.exists():
        try:
            timestamp = int(marker_file.read_text().strip())
            return datetime.fromtimestamp(timestamp)
        except:
            pass
    return None


def save_last_sync_time():
    """Save the current time as last sync time."""
    marker_file = BRAIN_DIR / ".last_sync"
    marker_file.write_text(str(int(datetime.now().timestamp())))


def sync_to_git() -> bool:
    """Commit and push changes to Git."""
    changed_files = get_changed_files()

    if not changed_files:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No changes to sync")
        return True

    # Filter ignored files
    files_to_commit = filter_changed_files(changed_files)

    if not files_to_commit:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Only ignored files changed")
        return True

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] Syncing {len(files_to_commit)} files..."
    )
    print(
        f"  Files: {', '.join(files_to_commit[:5])}"
        + ("..." if len(files_to_commit) > 5 else "")
    )

    try:
        # Add all files
        subprocess.run(
            [GIT_EXECUTABLE, "add", "-A"], cwd=BRAIN_DIR, check=True, timeout=30
        )

        # Commit with timestamp
        commit_message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(
            [GIT_EXECUTABLE, "commit", "-m", commit_message],
            cwd=BRAIN_DIR,
            check=True,
            timeout=30,
        )

        # Push to remote
        result = subprocess.run(
            [GIT_EXECUTABLE, "push", "origin", "master"],
            cwd=BRAIN_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            save_last_sync_time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Synced successfully")
            return True
        else:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Push failed: {result.stderr}"
            )
            return False

    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Git error: {e}")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Error: {e}")
        return False


def run_watcher(interval: int = 60):
    """Run continuous watcher."""
    print(f"🔄 Watching {BRAIN_DIR} for changes (every {interval}s)...")
    print("Press Ctrl+C to stop")
    print()

    last_commit_time = datetime.now()

    while True:
        try:
            # Check if enough time has passed since last commit
            time_since_last = (datetime.now() - last_commit_time).total_seconds()

            if time_since_last >= MINIMUM_COMMIT_INTERVAL:
                if sync_to_git():
                    last_commit_time = datetime.now()

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\n👋 Stopped")
            break


def run_schedule(interval_minutes: int = 5):
    """Run on schedule (for Windows Task Scheduler)."""
    print(f"📅 Running scheduled sync (every {interval_minutes} minutes)...")

    last_sync = get_last_sync_time()
    if last_sync:
        time_since = (datetime.now() - last_sync).total_seconds()
        if time_since < MINIMUM_COMMIT_INTERVAL:
            print(f"  Skipped - last sync {int(time_since)}s ago")
            return

    if sync_to_git():
        print("  ✓ Done")


def run_once():
    """Run single sync."""
    print("🔄 Running single sync...")
    sync_to_git()


def create_windows_task():
    """Create Windows Task Scheduler task."""
    script_path = Path(__file__).absolute()

    # Create a simple batch file wrapper
    bat_path = BRAIN_DIR / "autosync.bat"
    bat_content = f"""@echo off
cd /d "{BRAIN_DIR}"
python "{script_path}" --schedule
"""
    bat_path.write_text(bat_content)

    # Create scheduled task
    task_name = "BrainAutoSync"
    command = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc minute /mo 5 /f'

    print(f"Creating Windows scheduled task: {task_name}")
    print(f"  Command: {command}")

    try:
        subprocess.run(command, shell=True, check=True)
        print("✓ Task created successfully!")
        print(f"  Runs every 5 minutes")
        print(f'  To remove: schtasks /delete /tn "{task_name}" /f')
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating task: {e}")


def main():
    parser = argparse.ArgumentParser(description="Brain Auto-Sync")
    parser.add_argument("--watch", action="store_true", help="Continuous watching mode")
    parser.add_argument("--schedule", action="store_true", help="Run as scheduled task")
    parser.add_argument("--once", action="store_true", help="Run single sync")
    parser.add_argument(
        "--setup-task", action="store_true", help="Setup Windows Task Scheduler"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Watch interval in seconds"
    )

    args = parser.parse_args()

    if args.setup_task:
        create_windows_task()
    elif args.watch:
        run_watcher(args.interval)
    elif args.schedule:
        run_schedule()
    elif args.once:
        run_once()
    else:
        # Default: run once
        run_once()


if __name__ == "__main__":
    main()
