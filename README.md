# dropbox-extractor

A CLI tool that recursively extracts file names, paths, and URLs from a publicly shared Dropbox folder (including all nested subfolders). Outputs CSV or JSON.

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_ORG/dropbox-extractor
cd dropbox-extractor
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Get a Dropbox API token

You need your own free API token — **do not share or reuse someone else's**.

1. Go to [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
2. Click **Create app**
3. Choose **Scoped access** → **Full Dropbox**
4. Give it any name
5. Go to the **Permissions** tab → enable `files.metadata.read` and `sharing.read` → click **Submit**
6. Go to the **Settings** tab → scroll to **OAuth 2** → click **Generate** under "Generated access token"
7. Copy the token

> Once you've finished extracting the URLs you need, you can delete the token from the Settings tab.

### 4. Run it

```bash
python3 dropbox_extractor.py "https://www.dropbox.com/sh/YOUR_SHARED_LINK" \
  --token "YOUR_API_TOKEN" \
  --output results.csv
```

---

## Usage

```bash
python3 dropbox_extractor.py <shared_folder_url> [--token TOKEN] [--format csv|json] [--output FILE]
```

| Argument | Description |
|---|---|
| `shared_folder_url` | Dropbox shared folder URL |
| `--token` | Your Dropbox API token (or set `DROPBOX_API_TOKEN` env var) |
| `--format` | `csv` (default) or `json` |
| `--output` / `-o` | Output file path — defaults to stdout |

### Save to Desktop

```bash
python3 dropbox_extractor.py "FOLDER_URL" --token "YOUR_TOKEN" --output ~/Desktop/results.csv
```

### Set token as environment variable (avoids typing it every time)

```bash
export DROPBOX_API_TOKEN="YOUR_TOKEN"
python3 dropbox_extractor.py "FOLDER_URL" --output results.csv
```

---

## Output columns (CSV)

| Column | Description |
|---|---|
| `name` | File name |
| `path` | Full path within the folder (e.g. `Subfolder/Nested/file.pdf`) |
| `url` | Dropbox shared link — opens the file in browser |

---

## Notes

- The folder must be **publicly shared** ("Anyone with the link can view")
- Trashed files are excluded
- For very large folders the script may take a minute — it handles pagination automatically
- Once you've extracted the URLs you need, you can delete your API token in the Dropbox app settings
