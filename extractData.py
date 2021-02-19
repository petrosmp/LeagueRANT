"""
FOR FUNES
"""
import re

runes_srcfile = open("runeIDs.dat", "r")
runes = {}
for line in runes_srcfile.readlines():
    rune_id     = line.split(":")[0]
    rune_name   = line.split(":")[1][:-1]
    runes.update({rune_id:rune_name})



data = open("runes_vars.csv", "r")
rune_stats = {}
for line in data.readlines():
    stat_list = []
    line_items = line.split(';')
    rune_name = line_items[0].title()
    for item in line_items[1:]:
        if item and item != "\n":
            if item.endswith("\n"):
                item = item[:-1]
            stat_list.append(item)
    rune_stats.update({rune_name: stat_list})


for rune in rune_stats.keys():
    for stat in rune_stats[rune]:
        if "mins" in stat:
            index = rune_stats[rune].index(stat)
            if re.search(r"secs\d", rune_stats[rune][index+1]):
                secs1 = rune_stats
            continue

data.close()
