import argparse
import datetime
import math

from category import Category
import demo
from level import resolve_map_shortcuts
import sda
import srcom


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
        categories = [Category(c) for c in args.categories]

    sda_nicknames_by_name = sda.get_sda_nicknames()

    format_header = '{:15}  {:<20}  {:^8}  {:^10}  {:20}'
    format_line = '{:15}  {:20}  {:>8}  {:^10}  {:20}'
    format_empty = '{:15}  {}'
    print(format_header.format('Map/Category', 'Player', 'Time', 'Date', 'speedrun.com user'))
    for level in maps:
        if not args.categories:
            categories = [Category(c) for c in sda.get_categories_for_map(level.to_sda())]
        for category in categories:
            runs_srcom = srcom.SpeedrunDotComApi.get_runs(category.to_srcom(), level.to_srcom())
            runs_sda = sda.get_runs(category.to_sda(), level.to_sda())
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
                    map_category_string = f'{level}/{category}' if is_first_new_run else ''
                    print(format_line.format(map_category_string,
                        run_sda.name, run_sda.time, run_sda.date.isoformat(), user_string))
                    is_first_new_run = False

                    if args.submit_with_api_key:
                        srcom.SpeedrunDotComApi.submit(
                            run_sda, category.to_srcom(), level.to_srcom(),
                            user, args.submit_with_api_key)

            if is_first_new_run:
                print(format_empty.format(f'{level}/{category}', '[----- no new runs -----]'))


if __name__ == "__main__":
    main()
