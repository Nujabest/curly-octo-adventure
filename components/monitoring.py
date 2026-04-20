from functools import wraps

from flask import request, Response
from prometheus_client import REGISTRY
import psutil

from components.perf_metrics import RENDER_HISTORY

_MONITORING_USER = "admin"
_MONITORING_PASSWORD = "f1admin2026"

TAB_LABELS = {
    "overview": "Overview",
    "qualifying": "Qualifying",
    "replay": "Race Replay",
    "corner": "Corner Analysis",
    "tyre": "Tyre Analysis",
    "lap": "Lap Analysis",
    "progression": "Race Progression",
    "pitstops": "Pit Stops",
}


def configure_monitoring(user: str, password: str):
    global _MONITORING_USER, _MONITORING_PASSWORD
    _MONITORING_USER = user
    _MONITORING_PASSWORD = password


def require_monitoring_auth(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if (
            not auth
            or auth.username != _MONITORING_USER
            or auth.password != _MONITORING_PASSWORD
        ):
            return Response(
                "Access denied",
                401,
                {"WWW-Authenticate": 'Basic realm="F1 Monitoring"'},
            )
        return view_func(*args, **kwargs)

    return decorated


def _metric_counts_and_sums():
    counts, sums = {}, {}
    total_req = 0

    for metric in REGISTRY.collect():
        if metric.name != "f1_tab_render_seconds":
            continue
        for sample in metric.samples:
            tab = sample.labels.get("tab", "?")
            if sample.name == "f1_tab_render_seconds_count":
                counts[tab] = sample.value
                total_req += sample.value
            elif sample.name == "f1_tab_render_seconds_sum":
                sums[tab] = sample.value

    return counts, sums, total_req


def _row_color(avg):
    if avg > 5:
        return "#e8002d"
    if avg > 1:
        return "#00d2be"
    return "#39b54a"


def get_monitoring_context():
    proc = psutil.Process()
    ram_mb = proc.memory_info().rss / 1024 / 1024
    cpu_pct = proc.cpu_percent(interval=0.1)

    counts, sums, total_req = _metric_counts_and_sums()
    rows = sorted(
        [
            {
                "tab": TAB_LABELS.get(tab, tab),
                "calls": int(counts[tab]),
                "avg": round(sums.get(tab, 0) / counts[tab], 2) if counts[tab] else 0,
            }
            for tab in counts
        ],
        key=lambda row: row["avg"],
        reverse=True,
    )

    return {
        "last_render": (
            f"{RENDER_HISTORY[-1]['duration']:.2f}s" if RENDER_HISTORY else "—"
        ),
        "total_req": int(total_req),
        "ram_mb": ram_mb,
        "cpu_pct": cpu_pct,
        "rows": rows,
    }


def render_monitoring_page():
    ctx = get_monitoring_context()

    rows_html = "".join(
        f"<tr><td>{row['tab']}</td><td>{row['calls']}</td>"
        f"<td style='color:{_row_color(row['avg'])};font-weight:700'>{row['avg']:.2f}s</td></tr>"
        for row in ctx["rows"]
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>F1 Dashboard — Monitoring</title>
  <meta http-equiv="refresh" content="15">
  <style>
    body{{background:#08090d;color:#ccc;font-family:sans-serif;padding:32px;}}
    h1{{font-size:18px;letter-spacing:3px;color:#fff;margin-bottom:24px;}}
    .cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px;}}
    .card{{background:#0d0f14;border:1px solid #1e2229;border-radius:8px;padding:16px 22px;min-width:140px;}}
    .label{{font-size:10px;color:#555;letter-spacing:1.5px;font-weight:700;margin-bottom:6px;}}
    .value{{font-size:26px;font-weight:700;color:#fff;}}
    table{{width:100%;border-collapse:collapse;background:#0d0f14;border:1px solid #1e2229;border-radius:8px;}}
    th{{font-size:10px;color:#555;letter-spacing:1px;padding:10px 16px;text-align:left;border-bottom:1px solid #1e2229;}}
    td{{padding:10px 16px;font-size:13px;border-bottom:1px solid #12141a;}}
    tr:last-child td{{border-bottom:none;}}
    .legend{{font-size:11px;color:#555;margin-top:10px;}}
    .note{{font-size:10px;color:#333;margin-top:24px;}}
  </style>
</head>
<body>
  <h1>F1 DASHBOARD — MONITORING</h1>
  <div class="cards">
    <div class="card"><div class="label">LAST RENDER</div>
      <div class="value">{ctx["last_render"]}</div></div>
    <div class="card"><div class="label">TOTAL RENDERS</div>
      <div class="value">{ctx["total_req"]}</div></div>
    <div class="card"><div class="label">RAM USAGE</div>
      <div class="value" style="color:{'#e8002d' if ctx['ram_mb'] > 3000 else '#fff'}">{ctx["ram_mb"]:.0f} MB</div></div>
    <div class="card"><div class="label">CPU</div>
      <div class="value" style="color:{'#e8002d' if ctx['cpu_pct'] > 80 else '#fff'}">{ctx["cpu_pct"]:.1f}%</div></div>
  </div>
  <table>
    <thead><tr><th>TAB</th><th>CALLS</th><th>AVG RENDER</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="legend">&#x1F7E2; &lt;1s &nbsp; &#x1F535; 1–5s &nbsp; &#x1F534; &gt;5s</div>
  <div class="note">Auto-refresh every 15s</div>
</body>
</html>"""
