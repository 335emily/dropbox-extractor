#!/usr/bin/env python3
"""
dropbox_extractor.py — Recursively extract file names and paths from a public Dropbox shared folder.

Usage:
    python3 dropbox_extractor.py <shared_folder_url> [--format csv|json] [--output file.csv]

Requirements:
    pip3 install -r requirements.txt

Setup:
    Set your Dropbox API token as an environment variable:
        export DROPBOX_API_TOKEN="your_token_here"
    Or pass it directly: --token "your_token_here"
"""

import argparse
import csv
import json
import os
import sys

import dropbox
from dropbox.files import FolderMetadata, FileMetadata, SharedLink


def list_files(dbx, shared_link_url: str, subfolder_path: str = "", display_path: str = ""):
    cursor = None

    while True:
        try:
            if cursor:
                result = dbx.files_list_folder_continue(cursor)
            else:
                result = dbx.files_list_folder(
                    path=subfolder_path,
                    shared_link=SharedLink(url=shared_link_url),
                    recursive=False,
                )
        except dropbox.exceptions.ApiError as e:
            sys.exit(f"Error listing folder: {e}")

        for entry in result.entries:
            # Skip hidden macOS metadata files
            if entry.name.startswith("._") or entry.name == ".DS_Store":
                continue

            entry_display = f"{display_path}/{entry.name}" if display_path else entry.name
            entry_sub = f"{subfolder_path}/{entry.name}" if subfolder_path else f"/{entry.name}"

            if isinstance(entry, FolderMetadata):
                yield from list_files(dbx, shared_link_url, entry_sub, entry_display)
            elif isinstance(entry, FileMetadata):
                file_meta = dbx.sharing_get_shared_link_metadata(
                    url=shared_link_url,
                    path=entry_sub,
                )
                yield {
                    "name": entry.name,
                    "path": entry_display,
                    "url": file_meta.url,
                }

        if not result.has_more:
            break
        cursor = result.cursor


def write_csv(files, output):
    writer = csv.DictWriter(output, fieldnames=["name", "path", "url"])
    writer.writeheader()
    for f in files:
        writer.writerow(f)


def write_json(files, output):
    json.dump(list(files), output, indent=2)
    output.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively extract file names and paths from a public Dropbox shared folder."
    )
    parser.add_argument(
        "folder",
        help="Dropbox shared folder URL (e.g. https://www.dropbox.com/sh/...)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("DROPBOX_API_TOKEN"),
        help="Dropbox API token (or set DROPBOX_API_TOKEN env var)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
    )
    args = parser.parse_args()

    if not args.token:
        sys.exit(
            "Error: Dropbox API token required.\n"
            "Set it with: export DROPBOX_API_TOKEN='your_token'\n"
            "Or pass it with: --token 'your_token'\n\n"
            "Get a free token at: https://www.dropbox.com/developers/apps"
        )

    print(f"Connecting to Dropbox...", file=sys.stderr)
    dbx = dropbox.Dropbox(args.token)

    # Get the root folder name from the shared link metadata
    try:
        meta = dbx.sharing_get_shared_link_metadata(args.folder)
        root_name = meta.name
    except dropbox.exceptions.ApiError:
        root_name = ""

    print(f"Traversing shared folder...", file=sys.stderr)
    files = list_files(dbx, shared_link_url=args.folder, display_path=root_name)

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            if args.format == "json":
                write_json(files, f)
            else:
                write_csv(files, f)
        print(f"Done. Results written to: {args.output}", file=sys.stderr)
    else:
        if args.format == "json":
            write_json(files, sys.stdout)
        else:
            write_csv(files, sys.stdout)


if __name__ == "__main__":
    main()
