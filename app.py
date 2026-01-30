'''

This program sorts Renegades players into their games.


It prioritizes seniority first and then randomizes 


Player responses are stored in a downloaded .csv file (reading the .csv file may need to be changed based on the OS of the user)

	Each row of the csv is 1 player response per row

		Column F (index 5, since arrays start at 0) is the Class Year (2020, 2021, etc.)
		Column C (index 2, since arrays start at 0) is the First Name of the player
		In getMaxAndMinPlayers() the user is asked for the index of the first and last column of games
		The columns between these values (inclusive, counting up from 0), are preferences.
			The preference options are enumerated in POSSIBLE_PREFERENCES (they must be 1 character long and integers)
			Any responses in these cells besides a POSSIBLE_PREFERENCES value will be ignored
			If the player inputs multiple preferences of the same value (ie. 1 '1' and the rest are '5's),
				Then the leftmost one is encountered first and given preference
'''

import streamlit as st
import pandas as pd
import math
import random
import datetime
from pathlib import Path

st.set_page_config(layout="wide")
st.title("Renegades Game Distribution")
with st.container(border=True):
	SENIOR_YEAR = st.number_input("Senior Year", value=datetime.datetime.now().year)
	in_file = st.file_uploader("Upload CSV file")

#Debugging Values
# SENIOR_YEAR = 2023
JUNIOR_YEAR = SENIOR_YEAR + 1
SOPHMORE_YEAR = JUNIOR_YEAR + 1
FRESHMAN_YEAR = SOPHMORE_YEAR + 1

POSSIBLE_PREFERENCES = [1, 2, 3, 4, 5] #Be sure to order these in decreasing order of desireability from left to right

if in_file is None:
	st.stop()

suffix = Path(in_file.name).suffix.lower()
if suffix == ".csv":
	csv = pd.read_csv(in_file)
elif suffix == ".xlsx":
	csv = pd.read_excel(in_file)
else:
	st.error("Unsupported file type")
	st.stop()
csv = pd.DataFrame(csv)

cols = csv.columns.to_list() 

c = st.columns(3)
first_name_col = c[0].selectbox("Choose the first name column", cols, key="first_name_column")
last_name_col = c[1].selectbox("Choose the last name column", cols, key="last_name_column")
c = st.columns(3)
email_col = c[0].selectbox("Choose the email column", cols, key="email_column")
class_year_col = c[1].selectbox("Choose the class year column", cols, key="class_year_column")
pronouns_col = c[2].selectbox("Choose the pronouns column", cols, key="pronouns_column")

c = st.columns(3)
buddy_col = c[0].selectbox("Choose the buddy column", cols, key="buddy_column")
enemy_col = c[1].selectbox("Choose the enemy column", cols, key="enemy_column")
flags_cols = c[2].multiselect("Choose the flags columns", cols, key="flags_columns")

c = st.columns(3)
randseed = c[0].number_input("Random seed", value=1, min_value=1, max_value=1000000, key="randseed")
st.divider()

st.write("#### Choose the columns that represent the games")
game_cols_idx = st.dataframe(cols, selection_mode="multi-row", on_select="rerun", key="game_columns")["selection"]["rows"]
game_cols = [cols[i] for i in game_cols_idx]
# game_cols = st.multiselect("Choose the game columns", cols, key="game_columns")

st.write("#### Let us know a little bit more about each game")
games = {}
for col in game_cols:
	games[col] = {"players": []}
	c = st.columns(4)
	c[0].write(col)
	games[col]["min"] = c[1].number_input(f"Minimum players", value=3, min_value=1, max_value=20, key=f"min_{col}")
	games[col]["max"] = c[2].number_input(f"Maximum players", value=5, min_value=1, max_value=20, key=f"max_{col}")
	games[col]["short_name"] = c[3].text_input(f"Short name", value=col)


seniors = csv[csv["Class Year"] == SENIOR_YEAR]
juniors = csv[csv["Class Year"] == JUNIOR_YEAR]
sophmores = csv[csv["Class Year"] == SOPHMORE_YEAR]
freshmen = csv[csv["Class Year"] == FRESHMAN_YEAR]
other_year_students = csv[~csv["Class Year"].isin([SENIOR_YEAR, JUNIOR_YEAR, SOPHMORE_YEAR, FRESHMAN_YEAR])]

st.write(f"Found {len(seniors)} seniors, {len(juniors)} juniors, {len(sophmores)} sophmores, {len(freshmen)} freshmen, and {len(other_year_students)} other year students")

placement = {}
id_vars = [first_name_col, last_name_col, email_col, buddy_col, enemy_col, class_year_col, pronouns_col, *flags_cols]

for class_year in [seniors, juniors, sophmores, freshmen, other_year_students]:
	melted = class_year.melt(id_vars=id_vars, value_vars=game_cols, var_name="game", value_name="preference")
	melted = melted[melted["preference"].isin(POSSIBLE_PREFERENCES)]
	melted = melted.sort_values(by=id_vars + ["preference"])
	melted["game_pref"] = list(zip(melted["game"], melted["preference"].astype(int)))
	prefs_df = melted.groupby(id_vars, sort=False, dropna=False)["game_pref"].apply(list).reset_index()
	prefs_df = prefs_df.sample(frac=1, random_state=randseed)

	for index, row in prefs_df.iterrows():
		player_name = row[first_name_col] + " " + row[last_name_col] + " " + str(row[class_year_col])
		# + " " + str(row[class_year_col])
		buddy_enemy =  " *buddy[" + row[buddy_col] + "]" if pd.notna(row[buddy_col]) else ""
		buddy_enemy = buddy_enemy + "*enemy[" + row[enemy_col] + "]" if pd.notna(row[enemy_col]) else buddy_enemy
		player_prefs = row["game_pref"]
		placement[player_name] = None
		# for preference, rating in preferences.values.tolist()[0]:
		for x in player_prefs:
			preference = x[0]
			rating = x[1]
			if len(games[preference]["players"]) < games[preference]["max"]:
				if rating == 5:
					warning = "PLAYER IN PLEASE NO! "
				else:
					warning = ""
				# placement[player_name] = warning + games[preference]["short_name"] + " rating: " + str(rating) + buddy_enemy
				placement[player_name] = {
					"game": games[preference]["short_name"],
					"rating": rating,
					"class_year": row[class_year_col],
					"email": row[email_col],
					"pronouns": row[pronouns_col],
					"buddy": row[buddy_col],
					"enemy": row[enemy_col],
					"warning": warning,
					**{flag: row[flag] for flag in flags_cols}
				}
				# games[preference]["players"].append(warning + player_name + " rating: " + str(rating) + buddy_enemy)
				games[preference]["players"].append({
					"player": player_name,
					"rating": rating,
					"class_year": row[class_year_col],
					"email": row[email_col],
					"pronouns": row[pronouns_col],
					"buddy": row[buddy_col],
					"enemy": row[enemy_col],
					"warning": warning,
				})
				break

st.divider()
with st.container(border=True):
	st.subheader(":violet[Placements]")
	st.dataframe(pd.DataFrame.from_dict(placement, orient="index"), use_container_width=True)
st.divider()
for game in games:
	with st.container(border=True):
		color = 'red' if len(games[game]["players"]) < games[game]["min"] else 'green' if len(games[game]["players"]) == games[game]["max"] else 'orange'
		st.subheader(f':blue[{games[game]["short_name"]}]')
		st.write(f':{color}[{len(games[game]["players"])} out of [{games[game]["min"]}, {games[game]["max"]}] players]')
		st.dataframe(games[game]["players"], use_container_width=True)


st.divider()
st.write("## Summary")
with st.container(border=True):
	st.subheader("Underfilled Games")
	underfilled_games = [v["short_name"] for k,v in games.items() if len(v["players"]) < v["min"]]
	st.dataframe(underfilled_games, use_container_width=True)
with st.container(border=True):
	st.subheader("Unfilled Games")
	unfilled_games = [v["short_name"] for k,v in games.items() if len(v["players"]) > v["min"] and len(v["players"]) < v["max"]]
	st.dataframe(unfilled_games, use_container_width=True)
with st.container(border=True):
	st.subheader("Lonely Players")
	lonely_players = [k for k,v in placement.items() if v is None]
	st.dataframe(lonely_players, use_container_width=True)
with st.container(border=True):
	st.subheader("Potentially Sad Players")
	sad_player = [k for k,v in placement.items() if v["warning"] != ""]
	st.dataframe(sad_player, use_container_width=True)

