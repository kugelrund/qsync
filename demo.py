import datetime
import math
import os
import re
import subprocess
import tempfile
import urllib.request

import sys
sys.path.append("pydem")
import pydem
import messages


def get_exact_time(run):
    original_seconds = math.ceil(run.time)

    with tempfile.TemporaryDirectory() as tmpdirname:
        path_dz = os.path.join(tmpdirname, os.path.basename(run.demo))
        urllib.request.urlretrieve(run.demo, path_dz)
        cwd = os.getcwd()
        subprocess.check_output([os.path.join(cwd, 'dzip.exe'), '-x', path_dz],
                                cwd=tmpdirname)
        filename, _ = os.path.splitext(path_dz)

        decimals_txt = ''
        path_txt = f'{filename}.txt'
        if os.path.exists(path_txt):
            with open(path_txt, 'r') as f:
                text = f.read()
                if original_seconds >= 60:
                    minutes, seconds = divmod(original_seconds, 60)
                    matches_decimals = re.findall(f' {minutes}:{seconds}\.([0-9]+)', text)
                else:
                    matches_decimals = re.findall(f'(?::| )?{original_seconds}\.([0-9]+)', text)
                if matches_decimals:
                    # let's assume that the first time in this format is the
                    # actual time of the demo...
                    match_decimals = matches_decimals[0]
                    decimals_txt = match_decimals

        decimals_dem = ''
        path_dem = f'{filename}.dem'
        if os.path.exists(path_dem):
            demo = pydem.parse_demo(path_dem)
            messages_print = [m for block in demo.blocks for m in block.messages
                              if isinstance(m, messages.PrintMessage)]
            index_message_time = None
            indices_messages_final_time = [
                i for i in range(len(messages_print))
                if b"total time" in messages_print[i].text]
            if indices_messages_final_time:
                index_message_time = indices_messages_final_time[-1]
            else:
                indices_messages_time = [
                    i for i in range(len(messages_print))
                    if b"recorded time" in messages_print[i].text]
                if indices_messages_time:
                    index_message_time, = indices_messages_time
            if index_message_time:
                i = index_message_time + 1
                text_time = b''
                while not messages_print[i].text.endswith(b'\n'):
                    text_time += messages_print[i].text
                    i += 1
                text_time = text_time.decode('ascii').strip()
                minutes_and_seconds, decimals_dem = text_time.split('.')
                format_string = '%M:%S' if ':' in minutes_and_seconds else '%S'
                time_seconds = (
                    datetime.datetime.strptime(minutes_and_seconds, format_string) -
                    datetime.datetime.strptime("0", "%S")).total_seconds()
                assert time_seconds == original_seconds

        if decimals_dem and decimals_txt:
            if len(decimals_dem) < len(decimals_txt):
                print(f"Warning: Decimals in txt (.{decimals_txt}) are longer "
                      f"than decimals in demo (.{decimals_dem}). Using decimals"
                      "from txt.")
                return original_seconds + float('0.' + decimals_txt[:3])
            if (float('0.' + decimals_dem) < float('0.' + decimals_txt) or
                decimals_dem[:len(decimals_txt)] != decimals_txt):
                print(f"Warning: Decimals in txt (.{decimals_txt}) don't match "
                      f"decimals in demo (.{decimals_dem})")
        if decimals_dem:
            return original_seconds + float('0.' + decimals_dem[:3])
        return original_seconds + float('0.' + decimals_txt[:3])
