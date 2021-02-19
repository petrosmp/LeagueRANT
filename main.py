import sys
import os
import glob
import re
from extractData import rune_stats as rune_var_names

SERVER = "EUN1"        
SERVER_LIST = ["BR1", "EUN1", "EUW1", "LA1", "LA2", "NA1", "OCE", "RU1", "TR1", "JP1", "KR", "PBE"]
custom_path = 0

print("\n")                                                                                         # separate the programs output from the line that called it

def mapToDict(dictionary, key):
    """
    This function is only here for clarity reasons.
    Mapping something to dictionary[something] might or might not 
    get pretty hard to read when dealing with multi-dimensional dictionaries and dictionary lists
    """
    return dictionary[key]

def printHelp():
    """
    Display the help message
    """
    print("League Replay Analyzer v1.0")
    print("Usage: main.py <gameID> [OPTIONS <optional_arguments>]")
    print("Options:")
    print("-t | -T | --tilt                     tilt-related stats (mute stats, surrender votes, AFKs etc)")
    print("-i | -I | --items                    item related stats (build, wards, consumables etc)")
    print("-r | -R | --runes                    rune related stats (build, stats per rune)")
    print("-s | -S | --spells | --spell         spell info (times cast per ability, times cast per summ)")
    print("-o | -O | --obj | --objectives       objective related stats (obejctives stolen, stolen assists, damage etc)")
    print("-l | -L | --lag                      lag related info (ping, time spent DC'ed, time from last DC, AFK)")
    print("--latest                             automatically detect and analyze the last replay that was downloaded")
    print("--custom-path <path>                 analyze the file at the custom <path>. argument required")
    print("--server <server_name>               specify server (default: EUN1)")
    print("-a | -A | --all | --dump             print all stats")
    print("-h | -H | --help                     display this help\n")

def printRune(stat, summoner_stat_dict):
    """
    This function prints a rune and all the stats related to it.
    It also handles the obsecure case (RITO GEMS) of a stat being 
    spread across multiple stats.
    For example, a simple "Time Spent Doing Something (in minutes): 3:22"
    type stat might have the following structure:
    rune_stat_1 = 3
    rune_stat_2 = 2
    rune_stat_3 = 2
    But not always, so we also have to account for it being like this:
    rune_stat_1 = 3
    rune_stat_2 = 22
    rune_stat_3 = "mom's spaghetti"
    Kinda clean, ngl.
    """
    rune_name = runes[summoner_stat_dict[stat]]                                                     # map the rune to its name
    print(f"\n{rune_name}")                                                                         # print the rune's name
    rune_num = str(int(stat[-1:]))                                                                  # the double cast is completely useless (it's not like we're gonna catch exceptions and prevent our script from crashing, we're following RITO here)
    stat_text_list = rune_var_names[rune_name]                                                      # get the stat texts for the rune (e.g.: "Total Damage Dealt", "Total Respurces Gained" etc)
    skip = 0                                                                                        # a surprise tool that will help us later
    for index, text in enumerate(stat_text_list):                                                   # iterate through the stat text list
        if skip:                                                                                    # a surprise tool that will help us later
            skip-=1
            continue
        if "mins" in text:                                                                          # if the stat text contains the word "mins", the fun begins
            try:
                next_text = stat_text_list[index+1]                                                 # case#1:       there is another stat text after the "mins" one
                if "secs1" in next_text:                                                            # case#1.1:     the stat text after the "mins" text contains the substring "secs1". We have formatted the texts in such a way that this indicates that the stat is formatted in the first way shown in the function description
                    key = "PERK" + rune_num + "_VAR" + str(index+1)                                 #               In that case, we need to get 3 things: minutes, secs1 and secs 2
                    minutes = summoner_stat_dict[key]                                               #               get minutes
                    key = "PERK" + rune_num + "_VAR" + str(index+2)
                    secs1 = summoner_stat_dict[key]                                                 #               get secs1
                    key = "PERK" + rune_num + "_VAR" + str(index+3)
                    secs2 = summoner_stat_dict[key]                                                 #               get secs2
                    print(f"{text}: {minutes}:{secs1}{secs2}")                                      #               combine them all and print the stat text and the value
                    skip = 2                                                                        #               It's time for our surprise tool to help us by skipping the next 2 stats (we just printed them)
                    continue
                if "secs" in next_text:                                                             # case#1.2:     the stat text after the "mins" text contains the substring "secs" (without the 1). Because of the text formatting mentioned above (line 68), this indicates that the stat is formatted in the second way shown in the function description
                    key = "PERK" + rune_num + "_VAR" + str(index+1)                                 #               In that case, we need to get 2 things: minutes and secs
                    minutes = summoner_stat_dict[key]                                               #               get minutes
                    key = "PERK" + rune_num + "_VAR" + str(index+2)
                    secs = summoner_stat_dict[key]                                                  #               get seconds
                    print(f"{text}: {minutes}:{secs}")                                              #               combine and print
                    try:                                                                            # case#1.21     There is another stat after the minutes and the seconds
                        last_text = stat_text_list[index+2]
                        key = "PERK" + rune_num + "_VAR" + str(index+3)
                        value = summoner_stat_dict[key]                                             #               get the stat
                        print(f"{last_text}: {value}")                                              #               print it
                        skip = 1                                                                    #               skip the next stat (we just printed it)
                    except IndexError:                                                              # case#1.22     Ther is no other stat after the minutes and the seconds
                        skip = 1                                                                    #               skip the next stat
                        continue
            except IndexError:                                                                      # case#2        there is no other stat text after the "minutes" one
                pass                                                                                #               In that case, treat the minutes stat like any other, by doing the following:
        key = "PERK" + rune_num + "_VAR" + str(index+1)                                             # Forge the key to get the stat
        value = summoner_stat_dict[key]                                                             # Get the stat
        print(f"{text}: {value}")                                                                   # Print the stat text and the stat

# first of all, check if the help option is selected
if ('-h' in sys.argv) or ("-H" in sys.argv) or ("--help" in sys.argv) or (not sys.argv[1:]):
    printHelp()
    exit(0)


# parse and setup arguments
arguments = sys.argv[1:]
allShortArgs = []
removed_args = []
for arg in arguments:
    try:
        if arg.startswith('-') and arg[1]!='-':
            for char in arg[1:]:
                allShortArgs.append(char.lower())
                removed_args.append(arg)
    except IndexError:
        printHelp()
        exit(1)

arguments = list(set(arguments) - set(removed_args))                                                # not sure if this is good for performance or not but i like it so it stays here
verbose_mode = ('v' in allShortArgs) or ("--verbose" in arguments)                                  # verbose mode is checked often so this helps type less


# setup file path
if ("--server" in arguments):
    try:
        SERVER = sys.argv[sys.argv.index("--server") + 1]                                           # get the server that was specified
    except IndexError:                                                                              # means that nothing was specified after the --server flag
        print("You selected the set server option but did not provide a server name.")
        print("Usage: main.py <gameID> --server <server_name>")
        print("main.py -h | --help to display the complete help message\n\n")
        exit(2)
    if not SERVER in SERVER_LIST:                                                                   # very basic check-sanitization
        print(f"The name {SERVER} does not seem to be a valid League server name.")
        print("Are you sure you typed it correctly and in the correct order?")
        print("Valid League server names:")
        print(SERVER_LIST)
        print("main.py -h | --help to display the complete help message\n\n")
        exit(3)

homedir = os.path.expanduser('~')                                                                   # get the home directory of the user (not forging this with the username because sometimes they are different)
path = homedir + r'\Documents\League of Legends\Replays\\'

# latest game option
if ("--latest" in arguments):
    all_files = glob.glob(path+'*')                                                                 # get a list of files in the default league replay folder
    try:
        path = max(all_files, key=os.path.getctime)
    except ValueError:                                                                              # max() throws ValueError when the list argument is empty
        print(f"The default directory ({path}) seems to be empty! Please try again\n")
        exit(4)
else:
    try:
        gameID = int(sys.argv[1])                                                                   # if the latest game option is not selected, we'll have to forge the path ourselves
    except ValueError:
        print("Usage: main.py <gameID> [OPTIONS <optional_arguments>]")
        print("main.py -h | --help to display the complete help message\n")
        exit(5)
    try:
        path = homedir + r'\Documents\League of Legends\Replays\\'+SERVER+"-"+sys.argv[1]+".rofl"   # forge the path to the file (works if the user hasn't changed the location of the replay)
    except IndexError:
        print("\nUsage: main.py <gameID> [OPTIONS <optional_arguments>]")
        print("main.py -h | --help to display the complete help message\n\n")
        exit(6)

# custom path option
if "--custom-path" in arguments:                                                                                  
    custom_path = 1
    try:
        path = sys.argv[sys.argv.index("--custom-path")+1]
    except IndexError:
        print("You selected the custom path option but did not provide a custom path.")
        print("Usage: main.py <gameID> --custom-path <path>")
        print("main.py -h | --help to display the complete help message\n\n")
        exit(7)
    if (not path.endswith(".rofl")) and (not path.endswith(r".rofl'")) and (not path.endswith(r'rofl"')):       # need to add a better file check
        print("This is not a valid replay file. Are you sure you typed the path correctly?\n")
        exit(8)

# open the file
try:  
    src = open(path, "rb+") 
except FileNotFoundError:
    if custom_path:                                                                                 # if the user entered a custom path then anything in it can be wrong
        print("Couldn't find the file, or it was not a valid replay file. Are you sure you typed the path correctly?")
    else:
        print("Couldnt find the file! Are you sure you typed the game ID correctly?")               # if the user didn't choose a custom path, then only the gameID can be wrong
    print("\nUsage: main.py <gameID> [OPTIONS <optional_arguments>]")
    print("main.py -h | --help to display the complete help message\n\n")
    exit(2)

# keep the useful data
src.seek(287)                                                                                       # skip the first set of unreadable binary data
all_info = src.readline()                                                                           # surprisingly (?) all the info we are interested in is in a single line
delimeter1 = ','
info_list = all_info.partition(b'"statsJson":"[{\\')[2]                                             # skip some "useless" info about the game (duration etc)
info_list = info_list.partition(b'\\"}]"}')[0]                                                      # remove some unreadable binary data from the end of the line
info_list = info_list.decode().split(delimeter1)                                                    # decode() gets rid of the need for the "b" prefix when referring to our data.

# count stats
uniq_stats = []
for item in info_list:                                                                              # check every element of the info dump
    stat_name = item.partition(":")[0].strip(r'{\"}')                                               # keep only the name of the stat
    uniq_stats.append(stat_name)                                                                    # save stat name in the stat table
uniq_stats = list(dict.fromkeys(uniq_stats))                                                        # keep only unique stats
if verbose_mode:
    print(f"Found {len(uniq_stats)} unique stats")                                                  # display number of unique stats (should be the same for each player, ideally 152)

# extract stats and create a list of 10 dictionaries, each containing a summoner's stats
k=1
counter=1
summs_found=1
summoner_stats = []
player_stats = {}
for item in info_list:                                                                              # iterate all the information
    if item.partition(":")[0].strip(r'{\"}') == "ASSISTS":                                          # the "ASSISTS" stat is the first stat for every summoner. When we reach an "ASSISTS" stat, we know we are done with the last summoner
        if player_stats:                                                                            # the player_stats dictionary contains all the stats from the previous summoner. If it is not empty, we can add it to the summoner_stats list and reset it 
            summoner_stats.append(player_stats)                                                     # move the last player's stats to the list
        if verbose_mode:
            print(f"{len(player_stats)} stats found for this summoner")
        player_stats = {}                                                                           # reset the player_stats dictionary
        counter+=1
    if item.partition(":")[0].strip(r'{\"}') == "NAME":                                             # when a summoner name is found, add it to the dictionary under "Summoner name"
        summoner_name = item.partition(":")[2].strip(r'{\"}')                                       # get summoner name
        player_stats.update({"Summoner name": summoner_name})
        if verbose_mode:
            print(f"\n\nSummoner #{summs_found}, with name {summoner_name} (item {k})")
        counter=1                                                                                   # reset the stats/player counter
    else:                                                                                           # if the information item is not a name, it is a stat (we have made sure of that by cutting the list so it only contains useful information)
        stat = item.partition(":")[0].strip(r'{\"}')                                                # get the stat name
        value = item.partition(":")[2].strip(r'{\"}')                                               # get the stat value
        player_stats.update({stat:value})                                                           # add the stat_name:value pair to the player_stats dictionary
        #print(f"{stat}: {value}")
        counter+=1
    k+=1

# some extra stuff for the last summoner
summoner_stats.append(player_stats)                                                                 # last summoners' stats are left out of the list in the above loop, so we need to do some stuff manually
if verbose_mode:
    print(f"{len(summoner_stats[9])} stats found for this summoner")                                # print the number of stats we have after the merge

# map the runes to their IDs
runes_srcfile = open("runeIDs.dat", "r")                                                            # open the file with the rune-runeID assosiations to create a dictionary
runes = {}
for line in runes_srcfile.readlines():
    rune_id     = line.split(":")[0]                                                                # load the id for each rune
    rune_name   = line.split(":")[1][:-1]                                                           # load the name for each rune
    runes.update({rune_id:rune_name})                                                               # add the ID:rune pair to the dictionary

# map the items to their IDs
items_srcfile = open("itemIDs.dat", "r")                                                            # open the file with the item-itemID associations to create a dictionary
items = {}
for line in items_srcfile.readlines():
    item_id     = line.split(":")[0]                                                                # get item_ID
    item_name   = line.split(":")[1][1:-1]                                                          # get item_name
    items.update({item_id:item_name})                                                               # add the ID:item pair to the dictionary

# cleanup
src.close()
runes_srcfile.close()
items_srcfile.close()

""" format and display stats """

selected = {}                                                                                       # selected{} is a dictionary with all the stats that will be printed
options = ["tilt", "items", "runes", "spells", "objectives", "all"]

# tilt stats
if ('t' in allShortArgs) or ("--tilt" in arguments):
    tilt_stats = ["\nTilt-related stats:"]
    for stat in uniq_stats:
        if ("SURRENDER" in stat and not "GAME_ENDED" in stat) or ("PING" in stat) or ("NUM_DEATHS" in stat) or ("MUTE" in stat) or ("DISCONNECT" in stat) or ("TIME_SPENT_DEAD" in stat) or ("AFK" in stat):
            tilt_stats.append(stat)
    selected.update({"tilt":tilt_stats})

# item stats
if ('i' in allShortArgs) or ("--items" in arguments):
    item_stats = ["\nItem stats:"]
    for stat in uniq_stats:
        if ("ITEM" in stat) or ("PURCHASED" in stat) or ("BOUGHT" in stat):
            item_stats.append(stat)
    selected.update({"items":item_stats})

# rune stats
if ('r' in allShortArgs) or ("--runes" in arguments):
    rune_stats = ["\nRune stats:"]
    for stat in uniq_stats:
        if ("PERK" in stat) or ("KEYSTONE" in stat):
            rune_stats.append(stat)
    selected.update({"runes":rune_stats})

# spell info
if ('s' in allShortArgs) or ("--spell" in arguments) or ("--spells" in arguments):
    spell_stats = ["\nSpell stats:"]
    for stat in uniq_stats:
        if ("SPELL" in stat):
            spell_stats.append(stat)
    selected.update({"spells": spell_stats})

# objectives stats
if ('o' in allShortArgs) or ("--objectives" in arguments) or ("--obj" in arguments):
    objective_stats = ["\nObjective-related stats:"]
    for stat in uniq_stats:
        if ("BARON" in stat) or ("DRAGON" in stat) or ("OBJECTIVES" in stat) or ("BUILDINGS" in stat) or ("TURRET" in stat) or (stat == "WAS_AFK"):
            objective_stats.append(stat)
    selected.update({"objectives": objective_stats})

# all stats
if ('a' in allShortArgs) or ("--all" in arguments) or ("--dump" in arguments):
    all_stats = ["\nAll stats:"]
    all_stats = all_stats + uniq_stats
    selected.update({"all": all_stats})


for category in options:                                                                            # iterate through the options list
    if category in selected:                                                                        # if the category is a key in the selected{} dictionary
        print(selected[category][0])                                                                # print the corresponding text (When we put a category in the dictionary, the first element was the text that we want printed to "announce" the category)
        for summoner_stat_dict in summoner_stats:                                                   # iterate through the list of dictionaries that contain the stat names and values per summoner (each summoner has a dictionary {stat_name" stat_value})
            print(f"\n\n{summoner_stat_dict['Summoner name']} ({summoner_stat_dict['SKIN']}):")     # when printing a summoner's stats, print his summoner name and his champion name
            for stat in summoner_stat_dict.keys():                                                  # iterate through the keys (aka the stat_names) of each summoner's dictionary
                if stat in selected[category] and stat != "Summoner name" and stat != "SKIN":       # if a stat_name is in the selected dictionary under the current category, print it (we don't print summoner and champion names because they are printed before every "stat section" [see line 303])
                    if re.match("ITEM[0-6]", stat):                                                 # if the stat is an item (aka stat_name = ITEM1, ITEM2 ...), map it to its name
                        print(f"{stat}: {mapToDict(items,summoner_stat_dict[stat])}")
                        continue
                    if stat == "PERK_PRIMARY_STYLE":                                                # "PERK_PRIMARY_STYLE" is always right after the rune stats. Announce that other, non-numeric rune-related stats will be printed, and map it to its name
                        print("\nOther rune-related stats:")
                        print(f"{stat}: {mapToDict(runes, summoner_stat_dict[stat])}")
                        continue
                    if stat.startswith("KEYSTONE") or ("STYLE" in stat) or stat.startswith("STAT"): # if the stat is a rune, map it to its name
                        print(f"{stat}: {mapToDict(runes, summoner_stat_dict[stat])}")
                        continue
                    if "VAR" in stat:                                                               # if the stat is a rune substat (e.g. how much damage a rune dealt), ignore it. We will deal with it later
                        continue
                    if re.match("PERK[0-5]$", stat):                                                # if the stat is a rune (aka stat_name = PERK0, PERK1...), call the printRune function to map it to its name and print all stats related to it (the ones that we skipped in line 316)
                        printRune(stat, summoner_stat_dict)
                        continue
                    print(f"{stat}: {summoner_stat_dict[stat]}")                                    # if the stat is not a rune, item, summoner or champion name, print it as it is
            print("\n")
        print("\n\n\n")

exit(10)
