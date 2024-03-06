import os
import sys
from datetime import datetime

import pandas as pd

current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, "../"))

from modules.ergast_api import ErgastAPI, japan_timezone


def _get_target_season() -> int:
    """Get the season of the next grand prix"""
    # 当該のシーズンはその時点での年かその次の年である場合がある
    year_candidate_1 = datetime.now().year
    year_candidate_2 = year_candidate_1 + 1

    ergast_1 = ErgastAPI(year_candidate_1)
    ergast_2 = ErgastAPI(year_candidate_2)

    # 決勝レース時間の取得
    list_race_time_1 = [
        x if x is not None else None for x in ergast_1.get_event_time(event="race")
    ]
    list_race_time_2 = [
        x if x is not None else None for x in ergast_2.get_event_time(event="race")
    ]

    # 現在時刻以降の直近のレースの同定
    today = datetime.now(japan_timezone)
    for race_time_1 in list_race_time_1:
        if race_time_1 is None:
            continue
        elif race_time_1 > today:
            return year_candidate_1
    for race_time_2 in list_race_time_2:
        if race_time_2 is None:
            continue
        elif race_time_2 > today:
            return year_candidate_2


def get_this_season_calendar() -> pd.DataFrame:
    """Get this season's calendar"""
    year = _get_target_season()
    ergast = ErgastAPI(year)

    df = ergast.get_df_all_info()

    return df
