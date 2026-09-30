#!/usr/bin/env python3
"""Build the walkthrough page from a unified diff and a plan.

  build.py list  DIFF              print hunk ids
  build.py build DIFF PLAN OUT     write the HTML page
"""
import html, json, re, sys, urllib.request

D2H = "https://cdn.jsdelivr.net/npm/diff2html@3.4.56/bundles"
HLJS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles"


def parse(diff):
    files = {}
    for chunk in re.split(r"(?m)^(?=diff --git )", diff):
        if not chunk.strip():
            continue
        path = re.match(r"diff --git a/.* b/(.*)", chunk).group(1)
        header, *hunks = re.split(r"(?m)^(?=@@ )", chunk)
        files[path] = (header, hunks)
    return files


def hunk_ids(files):
    return [f"{p}#{i}" for p, (_, hs) in files.items() for i in range(1, len(hs) + 1)] + \
           [p for p, (_, hs) in files.items() if not hs]


def select(files, refs):
    """Rebuild a diff holding only the referenced hunks, file headers kept."""
    picked = {}
    for ref in refs:
        path, _, n = ref.partition("#")
        header, hunks = files[path]
        chosen = picked.setdefault(path, [header])
        chosen += hunks if not n else [hunks[int(n) - 1]]
    return "".join("".join(parts) for parts in picked.values())


def md(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text))


def fetch(url):
    return urllib.request.urlopen(url).read().decode()


def section(i, change, files, diffs):
    diffs.append(select(files, change.get("hunks", [])))
    issues = "".join(f'<p class="issue" id="issue-{i}-{j}">⚠ {md(t)}</p>'
                     for j, t in enumerate(change.get("issues", [])))
    return (f'<section class="change"><h2>{md(change["title"])}</h2>'
            f'<p>{md(change.get("explain", ""))}</p>{issues}'
            f'<div class="diff" data-i="{len(diffs) - 1}"></div></section>')


def build(diff_path, plan_path, out_path):
    files = parse(open(diff_path).read())
    plan = json.load(open(plan_path))
    changes, minor = plan.get("changes", []), plan.get("minor", [])

    used = {r for c in changes + minor for r in c.get("hunks", [])}
    ids = set(hunk_ids(files)) | set(files)
    if unknown := used - ids:
        sys.exit("Unknown hunk ids: " + ", ".join(sorted(unknown)))
    used |= {f"{p}#{i}" for p in used if p in files for i in range(1, len(files[p][1]) + 1)}
    skipped = {s["file"] for s in plan.get("skipped", [])}
    missing = [h for h in hunk_ids(files) if h not in used and h.partition("#")[0] not in skipped]
    if missing:
        sys.exit("Unassigned hunks:\n  " + "\n  ".join(missing))

    diffs = []
    body = "".join(section(i, c, files, diffs) for i, c in enumerate(changes))
    minor_html = "".join(section(f"m{i}", c, files, diffs) for i, c in enumerate(minor))
    skipped_html = "".join(f'<li><code>{html.escape(s["file"])}</code> — {md(s["text"])}</li>'
                           for s in plan.get("skipped", []))
    issue_links = "".join(
        f'<li><a href="#issue-{i}-{j}">{md(c["title"])}: {md(t)}</a></li>'
        for i, c in enumerate(changes) for j, t in enumerate(c.get("issues", [])))
    n_issues = sum(len(c.get("issues", [])) for c in changes)

    css = (f'@media (prefers-color-scheme: light) {{ {fetch(HLJS + "/github.min.css")} }}\n'
           f'@media (prefers-color-scheme: dark) {{ {fetch(HLJS + "/github-dark.min.css")} }}\n'
           + fetch(D2H + "/css/diff2html.min.css"))
    data = json.dumps(diffs).replace("<", "\\u003c")

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(plan["title"])}</title>
<style>{css}</style>
<style>
:root {{ --bg:#fff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --warn-bg:#fff8c5; --warn:#7d4e00; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --warn-bg:#3b2e00; --warn:#e3b341; }} }}
:root[data-theme="dark"] {{ --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --warn-bg:#3b2e00; --warn:#e3b341; }}
body {{ background:var(--bg); color:var(--fg); margin:0; padding:24px 16px;
  font:15px/1.5 -apple-system, "Segoe UI", system-ui, sans-serif; }}
main {{ max-width:1400px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 4px; }}
h2 {{ font-size:17px; margin:0 0 6px; }}
.meta {{ color:var(--muted); margin:0 0 20px; }}
.change {{ border-top:1px solid var(--line); padding:20px 0; }}
.change > p {{ margin:0 0 10px; max-width:80ch; }}
.issue {{ background:var(--warn-bg); color:var(--warn); padding:6px 10px; border-radius:6px; }}
.issues a {{ color:var(--warn); }}
code {{ font:13px ui-monospace, SFMono-Regular, Menlo, monospace; }}
details {{ border-top:1px solid var(--line); padding-top:16px; }}
summary {{ cursor:pointer; font-weight:600; }}
.diff {{ overflow-x:auto; }}
</style></head>
<body><main>
<h1>{html.escape(plan["title"])}</h1>
<p class="meta">{md(plan.get("target", ""))} · {len(changes)} changes · {n_issues} issues</p>
<p>{md(plan.get("summary", ""))}</p>
{f'<ul class="issues">{issue_links}</ul>' if issue_links else ""}
{body}
{f'<details><summary>Minor ({len(minor) + len(skipped)})</summary>{minor_html}<ul>{skipped_html}</ul></details>' if minor or skipped else ""}
</main>
<script type="application/json" id="diffs">{data}</script>
<script src="{D2H}/js/diff2html-ui.min.js"></script>
<script>
const diffs = JSON.parse(document.getElementById("diffs").textContent);
document.querySelectorAll(".diff").forEach(el => {{
  const diff = diffs[el.dataset.i];
  if (diff) new Diff2HtmlUI(el, diff, {{ outputFormat: "side-by-side", drawFileList: false,
    matching: "lines", highlight: true, colorScheme: "auto" }}).draw();
}});
</script>
</body></html>"""
    open(out_path, "w").write(page)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    if cmd == "list":
        print("\n".join(hunk_ids(parse(open(args[0]).read()))))
    else:
        build(*args)
