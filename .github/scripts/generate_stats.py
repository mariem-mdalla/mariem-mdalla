#!/usr/bin/env python3
"""
Generates assets/stats-card.svg and assets/streak-card.svg
in the same visual style as the project cards.
Reads live data from the GitHub GraphQL API.
"""
import os, json, urllib.request, urllib.error, datetime

TOKEN    = os.environ['GITHUB_TOKEN']
USERNAME = 'mariem-mdalla'

# ── Colours (keep in sync with project cards) ────────────────────────────────
BG      = '#0b0d14'
PRIMARY = '#8b7cff'
TEAL    = '#4fd1c5'
TEXT    = '#e9ebf5'
MUTED   = '#98a0b8'
BORDER  = '#ffffff'

QUERY = """
{
  user(login: "%s") {
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount date }
        }
      }
    }
    repositoriesContributedTo(
      contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]
    ) { totalCount }
  }
}
""" % USERNAME


def github_query(query):
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query}).encode(),
        headers={
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type':  'application/json',
            'User-Agent':    f'{USERNAME}-profile-action',
        },
        method='POST',
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# ── Fetch data ────────────────────────────────────────────────────────────────
data  = github_query(QUERY)['data']['user']
coll  = data['contributionsCollection']
stars = sum(r['stargazerCount'] for r in data['repositories']['nodes'])
commits        = coll['totalCommitContributions']
prs            = coll['totalPullRequestContributions']
issues         = coll['totalIssueContributions']
total_contrib  = coll['contributionCalendar']['totalContributions']
contributed_to = data['repositoriesContributedTo']['totalCount']

# ── Streak calculation from contribution calendar ─────────────────────────────
all_days = []
for week in coll['contributionCalendar']['weeks']:
    for day in week['contributionDays']:
        all_days.append((day['date'], day['contributionCount']))

all_days.sort(key=lambda x: x[0])
today_str = datetime.date.today().isoformat()

# current streak
current_streak = 0
for date, count in reversed(all_days):
    if date > today_str:
        continue
    if count > 0:
        current_streak += 1
    else:
        break

# longest streak
longest_streak, run = 0, 0
for _, count in all_days:
    if count > 0:
        run += 1
        longest_streak = max(longest_streak, run)
    else:
        run = 0

# streak start date
streak_start = ''
if current_streak > 0:
    active = [(d, c) for d, c in all_days if d <= today_str and c > 0]
    if active:
        streak_start = active[-current_streak][0] if current_streak <= len(active) else active[0][0]

# first contribution date (for "Since" label)
first_contrib = all_days[0][0] if all_days else today_str


def fmt_date(iso):
    """Convert '2026-10-09' -> 'Oct 9, 2026'"""
    if not iso:
        return ''
    try:
        d = datetime.date.fromisoformat(iso)
        months = ['Jan','Feb','Mar','Apr','May','Jun',
                  'Jul','Aug','Sep','Oct','Nov','Dec']
        return f"{months[d.month-1]} {d.day}"
    except Exception:
        return iso



# ── SVG helpers ───────────────────────────────────────────────────────────────
def card_wrap(w, h, glow_color, glow_cx, glow_cy, inner):
    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <radialGradient id="g" cx="{glow_cx}" cy="{glow_cy}" r="0.65" gradientUnits="objectBoundingBox">
    <stop offset="0" stop-color="{glow_color}" stop-opacity=".38"/>
    <stop offset="1" stop-color="{glow_color}" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="c"><rect width="{w}" height="{h}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#c)">
  <rect width="{w}" height="{h}" fill="{BG}"/>
  <rect width="{w}" height="{h}" fill="url(#g)"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="15" fill="none" stroke="{BORDER}" stroke-opacity=".07"/>
  {inner}
</g>
</svg>"""


# ── Stats card ────────────────────────────────────────────────────────────────
ROWS = [
    ('Total Stars Earned',      stars,          TEAL),
    ('Commits (this year)',      commits,        PRIMARY),
    ('Pull Requests',           prs,            TEAL),
    ('Issues',                  issues,         PRIMARY),
    ('Contributed to',          contributed_to, TEAL),
]

rows_svg = []
for i, (label, value, color) in enumerate(ROWS):
    y = 105 + i * 35
    rows_svg.append(
        f'<circle cx="40" cy="{y-5}" r="4" fill="{color}"/>'
        f'<text x="56" y="{y}" font-family="\'Segoe UI\',sans-serif" font-size="13.5" fill="{TEXT}" font-weight="500">{label}</text>'
        f'<text x="448" y="{y}" text-anchor="end" font-family="\'Segoe UI\',sans-serif" font-size="13.5" fill="{TEXT}">{value}</text>'
    )

stats_inner = f"""
  <rect x="24" y="24" width="36" height="3" rx="2" fill="{PRIMARY}"/>
  <text x="24" y="72" font-family="'Segoe UI',sans-serif" font-size="17" font-weight="700" fill="{TEXT}">GitHub Stats</text>
  {''.join(rows_svg)}
"""

stats_svg = card_wrap(490, 265, PRIMARY, '0.85', '0.15', stats_inner)


# ── Streak card ───────────────────────────────────────────────────────────────
streak_inner = f"""
  <rect x="24" y="24" width="36" height="3" rx="2" fill="{TEAL}"/>
  <text x="24" y="72" font-family="'Segoe UI',sans-serif" font-size="17" font-weight="700" fill="{TEXT}">Contribution Streak</text>

  <!-- Dividers -->
  <line x1="163" y1="105" x2="163" y2="235" stroke="{BORDER}" stroke-opacity=".08"/>
  <line x1="327" y1="105" x2="327" y2="235" stroke="{BORDER}" stroke-opacity=".08"/>

  <!-- Total Contributions -->
  <text x="81" y="150" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="38" font-weight="800" fill="{TEXT}">{total_contrib}</text>
  <text x="81" y="195" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="12" fill="{MUTED}">Total Contributions</text>
  <text x="81" y="218" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="11" fill="{MUTED}">{fmt_date(first_contrib)} - Present</text>

  <!-- Current Streak ring -->
  <circle cx="245" cy="142" r="38" fill="none" stroke="{PRIMARY}" stroke-width="4" stroke-opacity=".2"/>
  <circle cx="245" cy="142" r="38" fill="none" stroke="{PRIMARY}" stroke-width="4"
          stroke-dasharray="239" stroke-dashoffset="{max(0, 239 - int(239 * min(current_streak / 30, 1)))}"
          transform="rotate(-90 245 142)"/>
  <text x="245" y="153" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="30" font-weight="800" fill="{TEXT}">{current_streak}</text>
  <text x="245" y="195" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="12" fill="{TEAL}" font-weight="600">Current Streak</text>
  <text x="245" y="218" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="11" fill="{MUTED}">{fmt_date(streak_start) if streak_start else fmt_date(today_str)}</text>

  <!-- Longest Streak -->
  <text x="409" y="150" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="38" font-weight="800" fill="{TEXT}">{longest_streak}</text>
  <text x="409" y="195" text-anchor="middle" font-family="'Segoe UI',sans-serif" font-size="12" fill="{MUTED}">Longest Streak</text>
"""


streak_svg = card_wrap(490, 265, TEAL, '0.15', '0.85', streak_inner)


# ── Write files ───────────────────────────────────────────────────────────────
os.makedirs('assets', exist_ok=True)

with open('assets/stats-card.svg', 'w', encoding='utf-8') as f:
    f.write(stats_svg)

with open('assets/streak-card.svg', 'w', encoding='utf-8') as f:
    f.write(streak_svg)

print(f"Done. stars={stars} commits={commits} prs={prs} current_streak={current_streak} longest={longest_streak}")
