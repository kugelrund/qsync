import argparse
import datetime
import math

import demo
import sda
import srcom


def resolve_map_shortcuts(maps_and_shortcuts):
    maps = []
    for map in maps_and_shortcuts:
        if map == 'id':
            maps.extend(['e1m1', 'e1m2', 'e1m3', 'e1m4', 'e1m5', 'e1m6', 'e1m7', 'e1m8',
                         'e2m1', 'e2m2', 'e2m3', 'e2m4', 'e2m5', 'e2m6', 'e2m7',
                         'e3m1', 'e3m2', 'e3m3', 'e3m4', 'e3m5', 'e3m6', 'e3m7',
                         'e4m1', 'e4m2', 'e4m3', 'e4m4', 'e4m5', 'e4m6', 'e4m7', 'e4m8',
                         'ep1', 'ep2', 'ep3', 'ep4'])
        if map == 'hipnotic':
            maps.extend(['hip1m1', 'hip1m2', 'hip1m3', 'hip1m4', 'hip1m5',
                         'hip2m1', 'hip2m2', 'hip2m3', 'hip2m4', 'hip2m5', 'hip2m6',
                         'hip3m1', 'hip3m2', 'hip3m3', 'hip3m4', 'hipdm1',
                         'hipend', 'hip1', 'hip2', 'hip3'])
        if map == 'rogue':
            maps.extend(['r1m1', 'r1m2', 'r1m3', 'r1m4', 'r1m5', 'r1m6', 'r1m7',
                         'r2m1', 'r2m2', 'r2m3', 'r2m4', 'r2m5', 'r2m6', 'r2m7', 'r2m8',
                         'doe1', 'doe2'])
        else:
            maps.append(map)
    return maps


def is_same_run(run_srcom, run_sda, sda_nicknames):
    if math.floor(run_srcom.time) != math.floor(run_sda.time):
        return False
    if run_srcom.name.casefold() not in [n.casefold() for n in sda_nicknames]:
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('maps', type=str, nargs='*',
        help="Maps to process. 'id', 'hipnotic' and 'rogue' can be used as "
             "shortcuts for all id/hipnotic/rogue levels and episode runs.")
    parser.add_argument('--categories', type=str, nargs='*',
        help="Categories to process. Any combination of ER, EH, NR, NH.")
    parser.add_argument('--since', type=str,
        help="Only consider runs done after this date (ISO yyyy-dd-mm format).")
    parser.add_argument('--submit_with_api_key', type=str,
        help="Submit missing runs to speedrun.com with given speedrun.com API key.")
    args = parser.parse_args()

    maps = resolve_map_shortcuts(args.maps)
    if args.categories:
        categories = [c.upper() for c in args.categories]

    sda_nicknames_by_name = sda.get_sda_nicknames()

    format_header = '{:15}  {:<20}  {:^8}  {:^10}  {:20}'
    format_line = '{:15}  {:20}  {:>8}  {:^10}  {:20}'
    format_empty = '{:15}  {}'
    print(format_header.format('Map/Category', 'Player', 'Time', 'Date', 'speedrun.com user'))
    for map in maps:
        if not args.categories:
            categories = sda.get_categories_for_map(map)
        for category in categories:
            runs_srcom = srcom.SpeedrunDotComApi.get_runs(category, map)
            runs_sda = sda.get_runs(category, map)
            if args.since:
                since_date = datetime.date.fromisoformat(args.since)
                runs_sda = [r for r in runs_sda if r.date >= since_date]

            is_first_new_run = True
            for run_sda in runs_sda:
                if run_sda.name not in sda_nicknames_by_name:
                    sda_nicknames_by_name[run_sda.name] = [run_sda.name]

                sda_nicknames = sda_nicknames_by_name[run_sda.name]
                fitting_runs_srcom = [r for r in runs_srcom
                                      if is_same_run(r, run_sda, sda_nicknames)]

                if not fitting_runs_srcom:
                    user = srcom.SpeedrunDotComApi.get_user(sda_nicknames)
                    time = demo.get_exact_time(run_sda)
                    if time:
                        run_sda.time = time

                    user_string = user['weblink'] if user else 'Guest'
                    map_category_string = f'{map}/{category}' if is_first_new_run else ''
                    print(format_line.format(map_category_string,
                        run_sda.name, run_sda.time, run_sda.date.isoformat(), user_string))
                    is_first_new_run = False

                    if args.submit_with_api_key:
                        srcom.SpeedrunDotComApi.submit(run_sda, category, map, user, args.submit_with_api_key)

            if is_first_new_run:
                print(format_empty.format(f'{map}/{category}', '[----- no new runs -----]'))


if __name__ == "__main__":
    main()
