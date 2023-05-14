import datetime
import json
import re
import urllib.parse
import urllib.request

from run import Run


SPEEDRUN_DOT_COM_API_URL = 'https://www.speedrun.com/api/v1/'

GAME_IDS = ('nd2e7qd0', 'pdv2v46w', 'j1nwqw1p')

USER_AGENT_HEADER = {'User-Agent': 'Quake SDA Sync Tool'}

def get_level_ids():
    level_ids = dict()
    for game_id in GAME_IDS:
        with urllib.request.urlopen(urllib.request.Request(
                SPEEDRUN_DOT_COM_API_URL + f'games/{game_id}/levels',
                headers=USER_AGENT_HEADER)) as response:
            levels = json.load(response)['data']
        for l in levels:
            level_ids[l['name']] = l['id']
    return level_ids

def get_category_names():
    category_names = dict()
    for game_id in GAME_IDS:
        with urllib.request.urlopen(urllib.request.Request(
                SPEEDRUN_DOT_COM_API_URL + f'games/{game_id}/categories?miscellaneous=no',
                headers=USER_AGENT_HEADER)) as response:
            categories = json.load(response)['data']
        for c in categories:
            if c['type'] == 'per-level':
                assert c['id'] not in category_names
                category_names[c['id']] = c['name']
    return category_names

def get_srcom_demo_and_video(run):
    links = []
    if run['comment']:
        links += run['comment'].split()
    if run['videos']:
        links += [l['uri'] for l in run['videos']['links']]
    demo = ''
    video = ''
    for l in links:
        link = re.match('https?://[^\s]+', l)
        if link:
            link = link[0]
            if 'youtu' in link or 'twitch' in link:
                video = link
            else:
                demo = link
    return demo, video

def category_abbreviation_to_name(abbreviation):
    return {'ER': "Easy Run",
            'EH': "Easy 100%",
            'NR': "Nightmare Run",
            'NH': "Nightmare 100%"}[abbreviation]

def map_abbreviation_to_name(abbreviation):
    if abbreviation == 'ep1':
        return "All of Episode 1"
    elif abbreviation == 'ep2':
        return "All of Episode 2"
    elif abbreviation == 'ep3':
        return "All of Episode 3"
    elif abbreviation == 'ep4':
        return "All of Episode 4"
    elif abbreviation == 'hip1':
        return "All of Hip1"
    elif abbreviation == 'hip2':
        return "All of Hip2"
    elif abbreviation == 'hip3':
        return "All of Hip3"
    elif abbreviation == 'doe1':
        return "All of Rogue 1"
    elif abbreviation == 'doe2':
        return "All of Rogue 2"
    else:
        return abbreviation

class SpeedrunDotComApi:
    url = SPEEDRUN_DOT_COM_API_URL
    users = dict()
    level_ids = get_level_ids()
    category_names = get_category_names()
    category_ids = dict()
    nickname_to_userid = dict()

    @classmethod
    def get_collection(cls, request):
        collection = []
        while request:
            with urllib.request.urlopen(request) as response:
                response_json = json.load(response)
            collection.extend(response_json['data'])
            links_next = [link['uri'] for link in response_json['pagination']['links']
                          if link['rel'] == 'next']
            request = None
            if links_next:
                link_next, = links_next
                request = urllib.request.Request(link_next,
                                                 headers=USER_AGENT_HEADER)
        return collection

    @classmethod
    def get_user_name(cls, user_id):
        if user_id not in cls.users:
            with urllib.request.urlopen(urllib.request.Request(
                    cls.url + f'users/{user_id}',
                    headers=USER_AGENT_HEADER)) as response:
                cls.users[user_id] = json.load(response)['data']
                name = cls.users[user_id]['names']['international']
                assert name not in cls.nickname_to_userid
                cls.nickname_to_userid[name] = user_id
        return cls.users[user_id]['names']['international']

    @classmethod
    def get_run(cls, run):
        assert len(run['players']) == 1
        player = run['players'][0]
        if player['rel'] == 'user':
            name = cls.get_user_name(player['id'])
        else:
            name = player['name']
        date = None if not run['date'] else datetime.date.fromisoformat(run['date'])
        demo, video = get_srcom_demo_and_video(run)
        return Run(name, float(run['times']['primary_t']), date, demo, video)

    @classmethod
    def get_runs(cls, level_category, level_name):
        category_name = category_abbreviation_to_name(level_category)
        level_id = cls.level_ids[map_abbreviation_to_name(level_name)]
        runs_data = cls.get_collection(urllib.request.Request(
            cls.url + f'runs?level={level_id}&status=verified&max=200',
            headers=USER_AGENT_HEADER))
        runs = []
        for run in runs_data:
            category_id = run['category']
            if cls.category_names[category_id] == category_name:
                runs.append(cls.get_run(run))
                if level_id not in cls.category_ids:
                    cls.category_ids[level_id] = dict()
                cls.category_ids[level_id][category_name] = category_id
        return runs

    @classmethod
    def get_user_id_from_nickname(cls, nicknames):
        for nickname in nicknames:
            request = urllib.parse.urlencode({'lookup': nickname, 'max': 200})
            users = cls.get_collection(urllib.request.Request(
                cls.url + f'users?{request}', headers=USER_AGENT_HEADER))
            for user in users:
                if user['names']['international'].casefold() != nickname.casefold():
                    continue
                if user['id'] in cls.users:
                    # cls.users only contains Quake players, so this is probably
                    # who we are looking for
                    return user['id']
                else:
                    # check if the potential user actually plays Quake
                    request = urllib.parse.urlencode({
                        'user': user['id'], 'game': GAME_IDS[0]})
                    with urllib.request.urlopen(urllib.request.Request(
                            cls.url + f'runs?{request}',
                            headers=USER_AGENT_HEADER)) as response:
                        runs_data = json.load(response)['data']
                    if runs_data:
                        cls.users[user['id']] = user
                        return user['id']
        return None

    @classmethod
    def get_user(cls, nicknames):
        if not any(n in cls.nickname_to_userid for n in nicknames):
            user_id = cls.get_user_id_from_nickname(nicknames)
            for nickname in nicknames:
                cls.nickname_to_userid[nickname] = user_id
        known_nicknames = [n for n in nicknames if n in cls.nickname_to_userid]
        user_id = cls.nickname_to_userid[known_nicknames[0]]
        if not user_id:
            # this is a guest
            return None
        return cls.users[user_id]

    @classmethod
    def get_category_id(cls, level_category, level_id):
        category_name = category_abbreviation_to_name(level_category)
        if level_id not in cls.category_ids:
            cls.category_ids[level_id] = dict()
        if category_name not in cls.category_ids[level_id]:
            with urllib.request.urlopen(urllib.request.Request(
                    cls.url + f'levels/{level_id}/categories',
                    headers=USER_AGENT_HEADER)) as response:
                categories = json.load(response)['data']
            for category in categories:
                cls.category_ids[level_id][category['name']] = category['id']
        return cls.category_ids[level_id][category_name]

    @classmethod
    def submit(cls, run, level_category, level_name, user, api_key):
        level_id = cls.level_ids[map_abbreviation_to_name(level_name)]
        category_id = cls.get_category_id(level_category, level_id)

        data = json.dumps({"run": {
            "category": category_id,
            "level": level_id,
            "date": run.date.isoformat(),
            "platform": "8gej2n93",
            "verified": True,
            "times": {
                "ingame": run.time
            },
            "players": [
                {"rel": "user", "id": user['id']} if user else
                {"rel": "guest", "name": run.name},
            ],
            "emulated": False,
            "video": run.video,
            "comment": run.demo
        }})
        data_as_bytes = data.encode('utf-8')  # needs to be bytes
        header = {"X-Api-Key" : api_key,
                  'Content-Type': 'application/json',
                  'Content-Length': len(data_as_bytes)}
        header.update(USER_AGENT_HEADER)

        request =  urllib.request.Request(
            'https://www.speedrun.com/api/v1/runs', data_as_bytes, header)
        urllib.request.urlopen(request)
