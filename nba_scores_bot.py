import requests
import time
import schedule
from datetime import datetime, timedelta
import pytz

DISCORD_WEBHOOK_URL = “https://discord.com/api/webhooks/1486229880520835275/m5BPQ_A5JVCX2W3v8ozmMvSc5rUoVVWLIOo8XnotD7VgJ6bs2Ua9LXLKmd7RmD1nMmqS”

HEADERS = {
“User-Agent”: “Mozilla/5.0”,
“Referer”: “https://www.nba.com/”
}

def get_yesterdays_date():
et = pytz.timezone(“America/New_York”)
now = datetime.now(et)
target = now - timedelta(days=1)
return target.strftime(”%Y-%m-%d”)

def get_scores(date_str):
url = “https://stats.nba.com/stats/scoreboardv2?DayOffset=0&LeagueID=00&GameDate=” + date_str
try:
r = requests.get(url, headers=HEADERS, timeout=10)
return r.json()
except Exception as e:
print(“Error fetching scores: “ + str(e))
return None

def get_player_stats(game_id):
url = “https://stats.nba.com/stats/boxscoretraditionalv2?GameID=” + game_id + “&RangeType=0&StartPeriod=1&EndPeriod=10&StartRange=0&EndRange=28800”
try:
r = requests.get(url, headers=HEADERS, timeout=10)
return r.json()
except Exception as e:
print(“Error fetching player stats: “ + str(e))
return None

def get_stat_leaders(game_id):
data = get_player_stats(game_id)
if not data:
return None
try:
headers = data[“resultSets”][0][“headers”]
rows = data[“resultSets”][0][“rowSet”]
idx = {h: i for i, h in enumerate(headers)}
teams = {}
for row in rows:
if not row[idx[“MIN”]]:
continue
tid = row[idx[“TEAM_ID”]]
if tid not in teams:
teams[tid] = []
teams[tid].append(row)
leaders = {}
for tid, players in teams.items():
team_abbr = players[0][idx[“TEAM_ABBREVIATION”]]
def best(stat, p=players):
valid = [x for x in p if x[idx[stat]] is not None]
if not valid:
return (“N/A”, 0)
top = max(valid, key=lambda x: x[idx[stat]])
name = top[idx[“PLAYER_NAME”]].split(” “)[-1]
return (name, top[idx[stat]])
leaders[team_abbr] = {
“PTS”: best(“PTS”),
“REB”: best(“REB”),
“AST”: best(“AST”),
“STL”: best(“STL”),
“BLK”: best(“BLK”),
}
return leaders
except Exception as e:
print(“Error parsing stats: “ + str(e))
return None

def build_message(date_str):
data = get_scores(date_str)
if not data:
return None
try:
game_headers = data[“resultSets”][0][“headers”]
games = data[“resultSets”][0][“rowSet”]
line_score_headers = data[“resultSets”][1][“headers”]
line_scores = data[“resultSets”][1][“rowSet”]
if not games:
return “No NBA games on “ + date_str
idx_g = {h: i for i, h in enumerate(game_headers)}
idx_l = {h: i for i, h in enumerate(line_score_headers)}
game_map = {}
for row in line_scores:
gid = row[idx_l[“GAME_ID”]]
if gid not in game_map:
game_map[gid] = []
game_map[gid].append(row)
dt = datetime.strptime(date_str, “%Y-%m-%d”)
pretty_date = dt.strftime(”%B %d”)
lines = [“NBA Scores - “ + pretty_date, “”]
for game in games:
gid = game[idx_g[“GAME_ID”]]
if gid not in game_map or len(game_map[gid]) < 2:
continue
teams = game_map[gid]
t1 = teams[0]
t2 = teams[1]
t1_name = t1[idx_l[“TEAM_CITY_NAME”]] + “ “ + t1[idx_l[“TEAM_NAME”]]
t2_name = t2[idx_l[“TEAM_CITY_NAME”]] + “ “ + t2[idx_l[“TEAM_NAME”]]
t1_score = t1[idx_l[“PTS”]] or 0
t2_score = t2[idx_l[“PTS”]] or 0
lines.append(t1_name + “ “ + str(t1_score) + “ - “ + str(t2_score) + “ “ + t2_name)
leaders = get_stat_leaders(gid)
if leaders:
t1_abbr = t1[idx_l[“TEAM_ABBREVIATION”]]
t2_abbr = t2[idx_l[“TEAM_ABBREVIATION”]]
def fmt(abbr, stat):
if abbr in leaders and stat in leaders[abbr]:
name, val = leaders[abbr][stat]
return name + “ “ + str(val)
return “N/A”
stats_line = (
“PTS: “ + fmt(t1_abbr,“PTS”) + “ / “ + fmt(t2_abbr,“PTS”) + “ | “ +
“REB: “ + fmt(t1_abbr,“REB”) + “ / “ + fmt(t2_abbr,“REB”) + “ | “ +
“AST: “ + fmt(t1_abbr,“AST”) + “ / “ + fmt(t2_abbr,“AST”) + “ | “ +
“STL: “ + fmt(t1_abbr,“STL”) + “ / “ + fmt(t2_abbr,“STL”) + “ | “ +
“BLK: “ + fmt(t1_abbr,“BLK”) + “ / “ + fmt(t2_abbr,“BLK”)
)
lines.append(stats_line)
lines.append(””)
time.sleep(1)
return “\n”.join(lines)
except Exception as e:
print(“Error building message: “ + str(e))
return None

def post_scores():
print(“Posting scores…”)
date_str = get_yesterdays_date()
message = build_message(date_str)
if not message:
print(“No message to post”)
return
payload = {
“username”: “NBA Scores Bot”,
“content”: “`\n" + message + "\n`”
}
try:
resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
if resp.status_code == 204:
print(“Posted successfully!”)
else:
print(“Discord error “ + str(resp.status_code) + “: “ + resp.text)
except Exception as e:
print(“Failed to post: “ + str(e))

def main():
print(“NBA Scores Bot started”)
print(“Will post every night at 1am ET”)
schedule.every().day.at(“06:00”).do(post_scores)
while True:
schedule.run_pending()
time.sleep(30)

if **name** == “**main**”:
main()
