import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect("safedrive.db")
cur = conn.cursor()

cur.execute("""
    SELECT id, focus_score
    FROM focus_history
""")

rows = cur.fetchall()
conn.close()

if not rows:
    print("No focus history found")
    exit()

x = [r[0] for r in rows]
y = [r[1] for r in rows]

plt.figure(figsize=(10, 5))
plt.plot(x, y, linewidth=3)

plt.title("SafeDrive Focus Trend")
plt.xlabel("Time")
plt.ylabel("Focus Score")
plt.ylim(0, 100)
plt.grid(True)

plt.show()