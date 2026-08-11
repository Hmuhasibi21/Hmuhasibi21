#!/usr/bin/env python3
import html
import json
import os
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

USERNAME = os.getenv("GH_USERNAME", "Hmuhasibi21")
TOKEN = os.getenv("GH_TOKEN", "")
OUT = Path("assets")
OUT.mkdir(exist_ok=True)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "profile-stats-generator",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def gh_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def esc(value):
    return html.escape(str(value))


def pct(part, total):
    return 0 if total <= 0 else (part / total * 100.0)


def write_stats(profile, repos):
    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)
    forks = sum(r.get("forks_count", 0) for r in owned)
    watchers = sum(r.get("watchers_count", 0) for r in owned)

    now = datetime.now(timezone.utc)
    recent = 0
    for r in owned:
        pushed = r.get("pushed_at")
        if not pushed:
            continue
        try:
            dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            if (now - dt).days <= 30:
                recent += 1
        except ValueError:
            pass

    items = [
        ("Public repositories", profile.get("public_repos", len(owned))),
        ("Total stars", stars),
        ("Total forks", forks),
        ("Followers", profile.get("followers", 0)),
        ("Active repos (30d)", recent),
        ("Watching", watchers),
    ]

    rows = []
    for i, (label, value) in enumerate(items):
        col = i % 2
        row = i // 2
        x = 28 + col * 235
        y = 72 + row * 43
        rows.append(f'<text x="{x}" y="{y}" class="label">{esc(label)}</text>')
        rows.append(f'<text x="{x}" y="{y+20}" class="value">{esc(value)}</text>')

    updated = now.strftime("%Y-%m-%d %H:%M UTC")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="470" height="220" viewBox="0 0 470 220" role="img" aria-label="GitHub profile stats">
<style>
  .bg{{fill:#0d1117;stroke:#30363d;stroke-width:1}}
  .title{{fill:#f0f6fc;font:600 18px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
  .sub{{fill:#8b949e;font:12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
  .label{{fill:#8b949e;font:12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
  .value{{fill:#58a6ff;font:700 17px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
</style>
<rect class="bg" x="0.5" y="0.5" rx="14" width="469" height="219"/>
<circle cx="28" cy="28" r="5" fill="#3fb950"/>
<text x="42" y="34" class="title">GitHub Snapshot</text>
<text x="442" y="34" text-anchor="end" class="sub">@{esc(USERNAME)}</text>
{''.join(rows)}
<text x="28" y="205" class="sub">Generated via GitHub Actions - {esc(updated)}</text>
</svg>'''
    (OUT / "github-stats.svg").write_text(svg, encoding="utf-8")


def write_languages(repos):
    totals = defaultdict(int)
    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo.get("name")
        if not name:
            continue
        try:
            langs = gh_json(f"https://api.github.com/repos/{USERNAME}/{name}/languages")
            for lang, size in langs.items():
                totals[lang] += int(size)
        except Exception as e:
            print(f"warning: languages for {name}: {e}")

    total = sum(totals.values())
    top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:6]
    palette = ["#58a6ff", "#3fb950", "#d29922", "#bc8cff", "#f778ba", "#ff7b72"]

    rows = []
    y = 68
    for i, (lang, size) in enumerate(top):
        percent = pct(size, total)
        width = max(2, round(360 * percent / 100))
        color = palette[i % len(palette)]
        rows.append(f'<circle cx="28" cy="{y-4}" r="5" fill="{color}"/>')
        rows.append(f'<text x="42" y="{y}" class="lang">{esc(lang)}</text>')
        rows.append(f'<text x="442" y="{y}" text-anchor="end" class="pct">{percent:.1f}%</text>')
        rows.append(f'<rect x="28" y="{y+10}" width="360" height="7" rx="3.5" fill="#21262d"/>')
        rows.append(f'<rect x="28" y="{y+10}" width="{width}" height="7" rx="3.5" fill="{color}"/>')
        y += 31

    if not top:
        rows.append('<text x="28" y="90" class="sub">No public language data available yet.</text>')

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="470" height="285" viewBox="0 0 470 285" role="img" aria-label="Top public repository languages">
<style>
  .bg{{fill:#0d1117;stroke:#30363d;stroke-width:1}}
  .title{{fill:#f0f6fc;font:600 18px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
  .sub{{fill:#8b949e;font:12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
  .lang{{fill:#c9d1d9;font:600 12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
  .pct{{fill:#8b949e;font:12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif}}
</style>
<rect class="bg" x="0.5" y="0.5" rx="14" width="469" height="284"/>
<text x="28" y="34" class="title">Top Languages</text>
<text x="442" y="34" text-anchor="end" class="sub">public repositories</text>
{''.join(rows)}
<text x="28" y="270" class="sub">Generated via GitHub Actions - {esc(updated)}</text>
</svg>'''
    (OUT / "top-langs.svg").write_text(svg, encoding="utf-8")


def main():
    profile = gh_json(f"https://api.github.com/users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = gh_json(
            f"https://api.github.com/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100&page={page}"
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    write_stats(profile, repos)
    write_languages(repos)
    print(f"generated stats for {USERNAME}: {len(repos)} public repositories")


if __name__ == "__main__":
    main()
