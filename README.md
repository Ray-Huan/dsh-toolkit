# dsh-toolkit

Small, dependency-free CLI tools I use daily — and keep the code short enough to read in one sitting.

| Tool | What it does | Lang | Deps |
|---|---|---|---|
| [`tools/organize.py`](tools/organize.md) | Sort a messy folder into `类型/日期` buckets, dry-run by default, `--undo` to roll back | Python 3.8+ | none |
| [`tools/scrape.py`](tools/scrape.md) | Turn a list page into CSV / Excel with a tiny built-in HTML parser and CSS-ish selectors | Python 3.8+ | `openpyxl` only for `.xlsx` |

## Why no dependencies

Both tools started as "run it on a customer's machine that has nothing installed". A 200-line parser beats a 40 MB wheel when the target box is locked down, so `scrape.py` ships its own `HTMLParser` tree walker.

## Quick start

```bash
# 1. organize: look before touching anything
python tools/organize.py ~/Downloads

# 2. organize for real, then roll back if you dislike the layout
python tools/organize.py ~/Downloads --apply
python tools/organize.py ~/Downloads --undo

# 3. scrape: find the repeating element first
python tools/scrape.py https://example.com/list --dump

# 4. then extract
python tools/scrape.py https://example.com/list \
    --item "div.item" \
    --field "title=span.title" \
    --field "price=span.price" \
    --field "link=a@href" \
    --pages 3 --out result.csv
```

## Design notes

- **Dry-run first.** Every destructive operation (`organize.py --apply`) prints the plan and needs an explicit flag; `--undo` reads the manifest written during the run.
- **Fail soft.** Unreadable files, weird encodings (UTF-8 / GBK / GB18030) and missing selectors are reported per item instead of aborting the batch.
- **No network magic.** `scrape.py` sends a browser-ish UA, sleeps between pages (`--delay`), and refuses to guess selectors — `--dump` tells you which classes repeat.

## Limits

- `organize.py` moves files inside one volume; moving across drives copies + deletes.
- `scrape.py` handles static HTML. Pages rendered by JavaScript need a headless browser, which is out of scope on purpose.
- Both are single-file CLI tools — no server, no daemon.

## License

MIT
