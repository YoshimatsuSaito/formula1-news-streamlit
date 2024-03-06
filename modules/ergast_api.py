from datetime import datetime

import pandas as pd
import pytz
from ergast_py import Ergast
from tqdm import tqdm

japan_timezone = pytz.timezone("Asia/Tokyo")


class ErgastAPI:
    """Get information about designated season"""

    def __init__(self, season) -> None:
        self.season = season
        try:
            self.season_info = Ergast().season(self.season).get_races()
        except ValueError:
            raise ValueError(f"Season {self.season} does not exist")

    def get_circuit_id(self) -> list[str]:
        """Get circuit id of the season"""
        return [x.circuit.circuit_id for x in self.season_info]

    def get_circuit_name(self) -> list[str]:
        """Get circuit name of the season"""
        return [x.circuit.circuit_name for x in self.season_info]

    def get_event_time(self, event="race", timezone=japan_timezone) -> list[str]:
        """Get event datetime of the season"""
        if event == "race":
            return [
                (x.date.astimezone(timezone) if x.date is not None else None)
                for x in self.season_info
            ]
        elif event == "fp1":
            return [
                (
                    x.first_practice.astimezone(timezone)
                    if x.first_practice is not None
                    else None
                )
                for x in self.season_info
            ]
        elif event == "fp2":
            return [
                (
                    x.second_practice.astimezone(timezone)
                    if x.second_practice is not None
                    else None
                )
                for x in self.season_info
            ]
        elif event == "fp3":
            return [
                (
                    x.third_practice.astimezone(timezone)
                    if x.third_practice is not None
                    else None
                )
                for x in self.season_info
            ]
        elif event == "sprint":
            return [
                (x.sprint.astimezone(timezone) if x.sprint is not None else None)
                for x in self.season_info
            ]
        elif event == "qualifying":
            return [
                (
                    x.qualifying.astimezone(timezone)
                    if x.qualifying is not None
                    else None
                )
                for x in self.season_info
            ]
        return None

    def get_round_number(self) -> list[int]:
        """Get round number"""
        return [x.round_no for x in self.season_info]

    def get_gp_round_name(self) -> list[str]:
        """Get grand prix round and name"""
        return [f"Round {x.round_no} {x.race_name}" for x in self.season_info]

    def get_gp_name(self) -> list[str]:
        """Get grand prix name"""
        return [x.race_name for x in self.season_info]

    def get_url(self) -> list[str]:
        """Get url of the season"""
        return [x.url for x in self.season_info]

    def get_latitude(self) -> list[float]:
        """Get latitude of each grand prix"""
        return [x.circuit.location.latitude for x in self.season_info]

    def get_longtiude(self) -> list[float]:
        """Get longitude of each grand prix"""
        return [x.circuit.location.longitude for x in self.season_info]

    def get_latest_gp_index(self, timezone=japan_timezone) -> int:
        """Get index of latest grand prix
        NOTE: If all grand prix of the season was finished, return the last index
        """
        today = datetime.now(timezone)
        list_date = [x.date.astimezone(timezone) for x in self.season_info]
        if today > max(list_date):
            return list_date.index(max(list_date))
        latest_gp_date = min(x for x in list_date if x >= today)
        return list_date.index(latest_gp_date)

    def get_list_lap_time(self, year, target_round, driver):
        """Get lap times of a driver of year and round"""
        list_lap_time = []
        # Get lap times of winner (loop is for api limitation)
        for lap in tqdm(range(1, 101)):
            try:
                lap_time = (
                    Ergast()
                    .season(year)
                    .round(target_round)
                    .driver(driver)
                    .lap(lap)
                    .get_lap()
                    .laps[0]
                    .timings[0]
                    .time
                )
                lap_time = cvt_datetime_to_sec(lap_time)
                list_lap_time.append(lap_time)
            except:
                break
        return list_lap_time

    def get_df_all_info(self) -> pd.DataFrame:
        """Get all information"""
        df = pd.DataFrame(
            {
                "circuit_id": self.get_circuit_id(),
                "circuit_name": self.get_circuit_name(),
                "fp1": self.get_event_time(event="fp1"),
                "fp2": self.get_event_time(event="fp2"),
                "fp3": self.get_event_time(event="fp3"),
                "qualifying": self.get_event_time(event="qualifying"),
                "sprint": self.get_event_time(event="sprint"),
                "race": self.get_event_time(event="race"),
                "gp_round_name": self.get_gp_round_name(),
                "gp_name": self.get_gp_name(),
                "url": self.get_url(),
                "lat": self.get_latitude(),
                "lon": self.get_longtiude(),
                "n_round": self.get_round_number(),
            }
        )
        df["is_latest_gp"] = 0
        df.at[self.get_latest_gp_index(), "is_latest_gp"] = 1

        return df


def cvt_datetime_to_sec(datetime_value) -> float:
    """Convert datetime to sec"""
    return (
        datetime_value.hour * 3600
        + datetime_value.minute * 60
        + datetime_value.second
        + datetime_value.microsecond / 1000000
    )
