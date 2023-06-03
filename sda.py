import datetime
import re
import urllib.request

from run import Run


SDA_URL = 'https://quake.speeddemosarchive.com/quake/'

def get_history():
    sda_history_url = SDA_URL + 'history.txt'
    with urllib.request.urlopen(sda_history_url) as response:
        content = response.read().decode('cp1252')

    prelude, history_ER, history_EH, history_NR, history_NH, history_Marathon, runs_coop = re.split(
        '\*\*\*\* Easy runs \*\*\*\*|'
        '\*\*\*\* Easy 100% \*\*\*\*|'
        '\*\*\*\* Nightmare runs \*\*\*\*|'
        '\*\*\*\* Nightmare 100% \*\*\*\*|'
        '\*\*\*\* Marathon \*\*\*\*|'
        '\*\*\*\* Coop \*\*\*\*', content)

    history = dict()
    history['ER'] = history_ER.strip() + '\n'
    history['EH'] = history_EH.strip() + '\n'
    history['NR'] = history_NR.strip() + '\n'
    history['NH'] = history_NH.strip() + '\n'

    match_by_category = dict()
    history_Marathon = history_Marathon.strip()
    for line in history_Marathon.splitlines():
        if not line:
            continue
        new_line = None
        match_by_category['NH'] = re.match('Night ([A-z0-9]+) 100(.*)', line)
        match_by_category['EH'] = re.match('Easy ([A-z0-9]+) 100(.*)', line)
        match_by_category['NR'] = re.match('Nightmare ([A-z0-9]+)(.*)', line)
        match_by_category['ER'] = re.match('Easy ([A-z0-9]+)(.*)', line)
        for category in ['NH', 'EH', 'NR', 'ER']:
            if match_by_category[category]:
                current_category = category
                new_line = (match_by_category[category][1] +
                            match_by_category[category][2])
                break
        if not new_line:
            assert line.startswith((' ', '\t'))
            new_line = line
        history[current_category] += new_line + '\n'

    return history

def get_map_demo_names():
    config_url = SDA_URL + 'config'
    with urllib.request.urlopen(config_url) as response:
        content = response.read().decode('cp1252')
    _, content_levels, _ = re.split('\[levels\]|\[tables\]', content)
    # remove comments and empty lines
    content_levels = re.sub('#.*', '', content_levels).strip()

    map_to_demo_names = dict()
    for line in content_levels.splitlines():
        mapname, _, demoname, *_ = line.split(':')
        mapname = mapname.replace('%', '')
        map_to_demo_names[mapname] = demoname if demoname else mapname
    return map_to_demo_names

def extract_kill_count(line):
    kill_count_match = re.search('\[([0-9]+)\]', line)
    if kill_count_match:
        kill_count = int(kill_count_match[1])
        return line.replace(f'[{kill_count}]', ''), kill_count
    return line, None

def get_sda_run(run_data, category, demoname):
    if len(run_data) > 3:
        date, name, time_string, video = run_data
    else:
        date, name, time_string = run_data
        video = ''
    collapsed_time_string = time_string.replace(':', '')
    demo = SDA_URL + f'demos/{category}/{demoname}_{collapsed_time_string}.dz'

    minutes, seconds = time_string.split(':')
    time = datetime.timedelta(minutes=int(minutes),
                              seconds=int(seconds)).total_seconds()
    date = datetime.datetime.strptime(date, '%d.%m.%y').date()
    return Run(name, time, date, demo, video)

def get_all_runs():
    history = get_history()
    map_to_demo_names = get_map_demo_names()
    runs = dict()
    for category, lines in history.items():
        runs_this_category = dict()
        for line in lines.splitlines():
            run_data_match = '(?:\s\s+|\t)(?:\+\+ )?'
            if line.startswith((' ', '\t')):
                if kill_count:
                    line, new_kill_count = extract_kill_count(line)
                    if new_kill_count > kill_count:
                        kill_count = new_kill_count
                        runs_this_category[mapname] = []
                run_data = re.split(run_data_match, line.strip())
                runs_this_category[mapname].append(get_sda_run(run_data, category, map_to_demo_names[mapname]))
            else:
                line, kill_count = extract_kill_count(line)
                mapname, *run_data = re.split(run_data_match, line.strip())
                runs_this_category[mapname] = [get_sda_run(run_data, category, map_to_demo_names[mapname])]
        runs[category] = runs_this_category
    return runs

class SDA:
    runs = get_all_runs()

def get_categories_for_map(map):
    return [category for category in SDA.runs if map in SDA.runs[category]] 

def get_runs(category, map):
    return SDA.runs[category][map]

def get_sda_nicknames():
    config_url = SDA_URL + 'config'
    with urllib.request.urlopen(config_url) as response:
        content = response.read().decode('cp1252')
    _, content_players, _ = re.split('\[players\]|\[levels\]', content)
    # remove comments and empty lines
    content_players = re.sub('#.*', '', content_players).strip()

    nicknames = dict()
    for line in content_players.splitlines():
        names = line.split(':')
        assert names[0]
        nicknames[names[0]] = [name for name in names if name]
    nicknames['Conny Wernersson'].append('jukebox')
    nicknames['Jozsef Szalontai'].append('j0zzz')
    nicknames['Tony Hänninen'].append('kukkye')
    nicknames['Grzegorz Gladowski'].append('deniu')
    if 'Stuon' in nicknames:
        nicknames['Stuon'].append('stuon011')
    else:
        nicknames['Stuon'] = ['stuon011']
    return nicknames
