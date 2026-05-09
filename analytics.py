import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

plt.style.use("dark_background")

# Load DB
conn = sqlite3.connect("driver_reports.db")
df = pd.read_sql_query("SELECT * FROM reports", conn)
conn.close()

df["focus_score"] = (
    df["focus_score"]
    .astype(str)
    .str.replace("%", "", regex=False)
    .astype(float)
)

# KPIs
total_trips = len(df)
avg_focus = df["focus_score"].mean()
best_score = df["focus_score"].max()

total_alerts = (
    df["yawns"].sum()
    + df["eyes_closed"].sum()
    + df["phone_alerts"].sum()
    + df["look_away"].sum()
)

status_counts = df["status"].value_counts()

alert_breakdown = {
    "Yawns": df["yawns"].sum(),
    "Eyes Closed": df["eyes_closed"].sum(),
    "Phone": df["phone_alerts"].sum(),
    "Look Away": df["look_away"].sum()
}
# Load captured incidents
import os

capture_dir = "captures"

incident_files = []
if os.path.exists(capture_dir):
    incident_files = sorted(
        os.listdir(capture_dir),
        reverse=True
    )[:6]

# Figure
fig = plt.figure(figsize=(18, 10), facecolor="#0b132b")

gs = fig.add_gridspec(
    3,
    4,
    left=0.05,
    right=0.95,
    top=0.80,
    bottom=0.08,
    hspace=0.45,
    wspace=0.35
)
fig.suptitle(
    "SAFE DRIVE VISION ANALYTICS",
    fontsize=24,
    fontweight="bold",
    color="cyan"
)

# KPI cards
plt.figtext(0.08, 0.88, f"Trips\n{total_trips}",
            fontsize=18, ha="center", color="lime")

plt.figtext(0.32, 0.88, f"Avg Focus\n{avg_focus:.1f}%",
            fontsize=18, ha="center", color="cyan")

plt.figtext(0.56, 0.88, f"Best Score\n{best_score:.1f}%",
            fontsize=18, ha="center", color="gold")

plt.figtext(0.80, 0.88, f"Alerts\n{total_alerts}",
            fontsize=18, ha="center", color="tomato")

# Status chart
ax1 = fig.add_subplot(gs[0:2, 0:2])
ax1.set_facecolor("#1f2937")
ax1.bar(status_counts.index, status_counts.values)
ax1.set_title("Trip Status Distribution", color="white", fontsize=14)

# Alert chart
ax2 = fig.add_subplot(gs[0:2, 2])
ax2.set_facecolor("#1f2937")

total_alert_values = sum(alert_breakdown.values())

if total_alert_values == 0:
    ax2.text(
        0.5, 0.5,
        "No Alerts Yet",
        ha="center",
        va="center",
        fontsize=22,
        color="lime"
    )
    ax2.axis("off")
else:
    ax2.pie(
        list(alert_breakdown.values()),
        labels=list(alert_breakdown.keys()),
        autopct="%1.1f%%"
    )
    ax2.set_title("Alert Breakdown", color="white", fontsize=14)



# Focus trend
ax3 = fig.add_subplot(gs[2, 0:2])
ax3.set_facecolor("#1f2937")
ax3.plot(df["id"], df["focus_score"], linewidth=3, marker="o")
ax3.set_title("Focus Score Trend", color="white", fontsize=14)
ax3.set_xlabel("Trip ID")
ax3.set_ylabel("Score")
ax3.set_ylim(0, 100)
ax3.grid(alpha=0.3)

# Recent trips table
ax4 = fig.add_subplot(gs[2, 2])
ax4.axis("off")
ax4.set_facecolor("#1f2937")



table_df = df.copy()
table_df["alerts"] = (
    table_df["yawns"]
    + table_df["eyes_closed"]
    + table_df["phone_alerts"]
    + table_df["look_away"]
)

table_df = table_df[
    ["timestamp", "focus_score", "status", "alerts"]
].tail(5)

table = ax4.table(
    cellText=table_df.values,
    colLabels=["Date", "Score", "Status", "Alerts"],
    loc="center",
    cellLoc="center"
)

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.8)

for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor("white")

    if row == 0:  # header row
        cell.set_facecolor("#0f766e")
        cell.set_text_props(color="white", weight="bold")
    else:
        cell.set_facecolor("#1f2937")
        cell.set_text_props(color="white")

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 2)

ax4.set_title("Recent Trips", color="white", fontsize=14)

# Incident Gallery title
plt.figtext(
    0.88,
    0.62,
    "Incident Gallery",
    fontsize=18,
    color="white",
    ha="center",
    weight="bold"
)

# Incident Gallery title
plt.figtext(
    0.88,
    0.62,
    "Incident Gallery",
    fontsize=18,
    color="white",
    ha="center",
    weight="bold"
)

# Incident Gallery thumbnails
if incident_files:
    y_positions = [0.50, 0.38, 0.26]
    x_positions = [0.87, 0.97]

    idx = 0

    for y in y_positions:
        for x in x_positions:
            if idx >= len(incident_files):
                break

            img_path = os.path.join(capture_dir, incident_files[idx])

            try:
                incident_img = mpimg.imread(img_path)

                imagebox = OffsetImage(
                    incident_img,
                    zoom=0.12
                )

                ab = AnnotationBbox(
                    imagebox,
                    (x, y),
                    frameon=True,
                    box_alignment=(0.5, 0.5),
                    xycoords="figure fraction"
                )

                plt.gca().add_artist(ab)

            except Exception:
                pass

            idx += 1
plt.subplots_adjust(top=0.82, hspace=0.4, wspace=0.3)
plt.show()