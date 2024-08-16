"""This script contains functions for processing user inputs"""

import datetime

import gurobipy as gp
import numpy as np
import pandas as pd


def get_dates(year):
    """Return a dataframe of dates for the given year. The dataframe will have
    365 rows, one for each day of the year. The columns are 'date' and 'hour'.
    """
    # Create dates to concatenate with the new dataframes
    dates = pd.DataFrame(
        {"date": pd.date_range(start=str(year), periods=366, freq="D")}
    )
    # Remove 29th Feb because we do not deal with them
    dates = dates.loc[dates.date.dt.strftime("%m-%d") != "02-29"]
    # Remove 1st Jan of the next year in case it is included when it is not a leap year
    dates = dates.loc[dates.date.dt.strftime("%Y-%m-%d") != f"{year+1}-01-01"]

    # In case we need three columns: date, hour, and day
    dates = dates.loc[dates.index.repeat(24)]
    dates["hour"] = np.tile(range(1, 25), 365)
    dates = dates.reset_index(drop=True)
    return dates


def create_init_condition(thermal_units: list) -> dict[(str, int), dict]:
    """Return dicts of system statuses in the format {(unit, hour): value}"""
    # Assume thermal units in the systems are offline at the beginning
    initial_p = {unit_g: 0 for unit_g in thermal_units}
    initial_u = initial_p.copy()
    initial_v = initial_p.copy()
    initial_w = initial_p.copy()

    # Thermal units do not carry any minimum up and down time at the beginning
    initial_min_on = {unit_g: 0 for unit_g in thermal_units}
    initial_min_off = initial_min_on.copy()

    return {
        "initial_p": initial_p,
        "initial_u": initial_u,
        "initial_v": initial_v,
        "initial_w": initial_w,
        "initial_min_on": initial_min_on,
        "initial_min_off": initial_min_off,
    }


def get_sim_period(step_k: int, sim_horizon: int) -> range:
    """
    Generates indices for a rolling horizon simulation.

    Args:
        k: The current simulation step.
        T: The simulation horizon.

    Returns:
        A range of indices for the current step.
    """
    start_index = (step_k - 1) * sim_horizon + 1
    end_index = step_k * sim_horizon
    return range(start_index, end_index + 1)


def get_unit_hour_from_varnam(var_name: str) -> (str, int):
    """Get the unit and hour from the variable name.

    Args:
        var_name: The name of the variable.

    Returns:
        The unit and hour.

    """
    var_name = var_name.replace("[", "").replace("]", "")
    var_name = var_name.split(",")
    unit = var_name[0]
    hour = int(var_name[1])

    return unit, hour


def get_edge_hour_from_varname(var_name: str) -> (str, str, int):
    """Get the edge and hour from the variable name: flow[a,b,t].

    Args:
        var_name: The name of the variable.

    Returns:
        The edge and hour.

    """
    var_name = var_name.replace("flow[", "").replace("]", "")
    var_name = var_name.split(",")
    edge = (var_name[0], var_name[1])
    hour = int(var_name[2])

    return edge, hour


def get_nodehour(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Extract the node and hour information
    pat_node_time = r"(\w+)\[(.+),(\d+)\]"
    out_df = df["varname"].str.extract(pat_node_time, expand=True)
    out_df.columns = ["vartype", "node", "hour"]
    out_df["hour"] = out_df["hour"].astype("int")
    out_df = pd.concat([out_df, df["value"]], axis=1)
    return out_df


def get_nodehour_flow(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Flow is in the (node_a, node_b, t) format
    pat_node_time = r"flow\[(.+),(.+),(\d+)\]"
    out_df = df["varname"].str.extract(pat_node_time, expand=True)
    out_df.columns = ["node_a", "node_b", "hour"]
    out_df["hour"] = out_df["hour"].astype("int")
    out_df = pd.concat([out_df, df["value"]], axis=1)
    return out_df


def get_nodehour_sys(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Extract the node and hour information
    pat_node_time = r"(.+)\[(\d+)\]"
    out_df = df["varname"].str.extract(pat_node_time, expand=True)
    out_df.columns = ["vartype", "hour"]
    out_df["hour"] = out_df["hour"].astype("int")
    out_df = pd.concat([out_df, df["value"]], axis=1)
    return out_df


def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M")
