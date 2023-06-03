sda_levelname_to_srcom_levelname = {
    'ep1': "All of Episode 1",
    'ep2': "All of Episode 2",
    'ep3': "All of Episode 3",
    'ep4': "All of Episode 4",
    'hip1': "All of Hip1",
    'hip2': "All of Hip2",
    'hip3': "All of Hip3",
    'doe1': "All of Rogue 1",
    'doe2': "All of Rogue 2",
}
srcom_levelname_to_sda_levelname = {
    v: k for k, v in sda_levelname_to_srcom_levelname.items()
}


class Level:
    def __init__(self, name):
        self.name = srcom_levelname_to_sda_levelname.get(name, name)

    def to_sda(self):
        return self.name

    def to_srcom(self):
        return sda_levelname_to_srcom_levelname.get(self.name, self.name)

    def __str__(self):
        return self.name


def resolve_map_shortcuts(maps_and_shortcuts):
    maps = []
    for map in maps_and_shortcuts:
        if map == 'id':
            maps.extend(['e1m1', 'e1m2', 'e1m3', 'e1m4', 'e1m5', 'e1m6', 'e1m7', 'e1m8',
                         'e2m1', 'e2m2', 'e2m3', 'e2m4', 'e2m5', 'e2m6', 'e2m7',
                         'e3m1', 'e3m2', 'e3m3', 'e3m4', 'e3m5', 'e3m6', 'e3m7',
                         'e4m1', 'e4m2', 'e4m3', 'e4m4', 'e4m5', 'e4m6', 'e4m7', 'e4m8',
                         'ep1', 'ep2', 'ep3', 'ep4'])
        elif map == 'hipnotic':
            maps.extend(['hip1m1', 'hip1m2', 'hip1m3', 'hip1m4', 'hip1m5',
                         'hip2m1', 'hip2m2', 'hip2m3', 'hip2m4', 'hip2m5', 'hip2m6',
                         'hip3m1', 'hip3m2', 'hip3m3', 'hip3m4', 'hipdm1',
                         'hipend', 'hip1', 'hip2', 'hip3'])
        elif map == 'rogue':
            maps.extend(['r1m1', 'r1m2', 'r1m3', 'r1m4', 'r1m5', 'r1m6', 'r1m7',
                         'r2m1', 'r2m2', 'r2m3', 'r2m4', 'r2m5', 'r2m6', 'r2m7', 'r2m8',
                         'doe1', 'doe2'])
        else:
            maps.append(map)
    return [Level(m) for m in maps]
