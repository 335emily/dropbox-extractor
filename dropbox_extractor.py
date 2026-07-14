#!/usr/bin/env python3
"""
dropbox_extractor.py — Recursively extract file URLs from a public Dropbox shared folder.

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
from dropbox.files import FolderMetadata, FileMetadata, ListFolderArg, SharedLink


def list_files_recursive(dbx, path: str = "", shared_link_url: str = None, folder_path: str = ""):
    shared_link = SharedLink(url=shared_link_url) if shared_link_url else None

    try:
        if shared_link:
            result = dbx.files_list_folder(
                path=path,
                shared_link=shared_link,
                recursive=False,
            )
        else:
            result = dbx.files_list_folder(path=path, recursive=False)
    except dropbox.exceptions.ApiError as e:
        sys.exit(f"Error listing folder: {e}")

    while True:
        for entry in result.entries:
            entry_path = f"{folder_path}/{entry.name}" if folder_path else entry.name
            if isinstance(entry, FolderMetadata):
                yield from list_files_recursive(
                    dbx,
                    path=entry.path_lower,
                    shared_link_url=shared_link_url,
                    folder_path=entry_path,
                )
            elif isinstance(entry, FileMetadata):
                # Construct a direct shared link for the file
                try:
                    link_meta = dbx.sharing_create_shared_link_with_settings(entry.path_lower)
                    url = link_meta.url
                except dropbox.exceptions.ApiError:
                    # Link may already exist — fetch it
                    try:
                        links = dbx.sharing_list_shared_links(path=entry.path_lower, direct_only=True)
                        url = links.links[0].url if links.links else ""
                    except dropbox.exceptions.ApiError:
                        url = ""
                yield {
                    "name": entry.name,
                    "path": entry_path,
                    "url": url,
                }

        if not result.has_more:
            break
        result = dbx.files_list_folder_continue(result.cursor)


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
        description="Recursively extract file URLs from a public Dropbox shared folder."
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

    print(f"Traversing shared folder...", file=sys.stderr)
    files = list_files_recursive(dbx, path="", shared_link_url=args.folder)

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
