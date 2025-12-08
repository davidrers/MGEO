"""
Practical 4 – Functional approach

This script:
- Uses plain functions to work with building data.
- Parses height info into min / max / mid height (in meters).
- Computes a simple Urban Heat Island (UHI) risk score per building.
- Reads data from PostgreSQL/PostGIS.
- Creates the 'public.enschede_building' table from a SQL file if needed.

Note: GenAI tools were used for commenting and styling purposes only. 
"""

from typing import Optional, Tuple, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# ----------------------------------------------------------------------
# Global constants and DB config
# ----------------------------------------------------------------------

# UHI formula weights
HEIGHT_FACTOR = 0.6   # how much height matters
AREA_FACTOR = 0.4     # how much area matters

# Typical storey heights
RESIDENTIAL_STOREY_HEIGHT = 3.0   # meters per floor
OTHER_STOREY_HEIGHT = 3.5         # meters per floor (commercial, industrial, other)

# Usage-dependent weights for UHI risk
USAGE_WEIGHTS = {
    "residential": 1.0,
    "commercial": 1.3,
    "industrial": 1.6,
    "other": 1.0,
}


# ----------------------------------------------------------------------
# DB utilities
# ----------------------------------------------------------------------


def connect_to_db(config: Dict[str, Any]):
    """
    Open a connection to PostgreSQL using the given settings.

    Parameters
    ----------
    config : dict
        Dictionary with keys 'host', 'database', 'user', 'password', 'port'.

    Returns
    -------
    connection
        psycopg2 connection object.
    """
    return psycopg2.connect(
        host=config["host"],
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
        port=config["port"],
    )


def ensure_table_from_sql(
    conn,
    table_name: str,
    sql_path: str,
) -> None:
    """
    Make sure a table exists. If it does not, create it from a SQL file.

    Parameters
    ----------
    conn : connection
        Open psycopg2 connection.
    table_name : str
        Full table name, e.g. 'public.enschede_building'.
    sql_path : str
        Path to a SQL file that creates/populates this table.
    """
    with conn.cursor() as cur:
        # Check if the table already exists
        cur.execute("SELECT to_regclass(%s);", (table_name,))
        exists = cur.fetchone()[0] is not None

        if exists:
            # Table is already there, nothing to do
            return

        # Table is missing → read and execute the SQL file
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_text = f.read()

        cur.execute(sql_text)
        conn.commit()


def fetch_building_rows(
    conn,
    table_name: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Read building rows from a table.

    Parameters
    ----------
    conn : connection
        Open psycopg2 connection.
    table_name : str
        Full table name, e.g. 'public.enschede_building'.
    limit : int, optional
        Max number of rows to fetch. If None, fetch all rows.

    Returns
    -------
    list of dict
        Each dict has at least:
        'id', 'occupancy', 'height', 'height_type', 'height_value', 'area'.
    """
    rows: List[Dict[str, Any]] = []

    sql = f"""
        SELECT
            id,
            occupancy,
            height,
            height_type,
            height_value,
            ST_Area(ST_SetSRID(wkb_geometry, 4326)::geography) AS area
        FROM {table_name}
    """
    if limit is not None:
        sql += " LIMIT %s"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if limit is not None:
            cur.execute(sql, (limit,))
        else:
            cur.execute(sql)

        for record in cur.fetchall():
            rows.append(dict(record))

    return rows


# ----------------------------------------------------------------------
# Height + usage helpers 
# ----------------------------------------------------------------------


def map_occupancy_to_usage(occ: Optional[str]) -> str:
    """
    Map an occupancy code into a simple usage label.

    Parameters
    ----------
    occ : str or None
        Occupancy code from the database (e.g. 'RES', 'COM1', 'IND2').

    Returns
    -------
    str
        One of: 'residential', 'commercial', 'industrial', 'other'.
    """
    if not occ:
        return "other"

    occ = occ.upper()

    # Residential codes
    if occ.startswith("RES") or occ in {"MIX1", "MIX4", "MIX5"}:
        return "residential"

    # Commercial codes
    if occ.startswith("COM"):
        return "commercial"

    # Industrial codes
    if occ.startswith("IND"):
        return "industrial"

    # Everything else (GOV*, EDU*, ASS*, AGR*, UNK, ...)
    return "other"


def get_storey_height(usage: str) -> float:
    """
    Return a typical storey height for a given usage type.

    Parameters
    ----------
    usage : str
        Usage label ('residential', 'commercial', 'industrial', 'other').

    Returns
    -------
    float
        Storey height in meters.
    """
    if usage == "residential":
        return RESIDENTIAL_STOREY_HEIGHT
    # For commercial, industrial, and other, use the same height
    return OTHER_STOREY_HEIGHT


def strip_height_prefix(s: str) -> str:
    """
    Remove prefixes like 'HBET:' or 'H:' from a height string.

    Parameters
    ----------
    s : str
        Raw height string with possible prefix.

    Returns
    -------
    str
        Clean height string without prefix and surrounding spaces.
    """
    if ":" in s:
        s = s.split(":", 1)[1]
    return s.strip()


def parse_heights(
    height_type: Optional[str],
    height: Optional[str],
    height_value: Optional[str],
    storey_height: float,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Turn height fields into min / max / mid height (meters).

    Parameters
    ----------
    height_type : str or None
        Type of height info ('H', 'HBET', 'HEX', 'HHT', or None).
    height : str or None
        Raw height string from the database (may have prefixes).
    height_value : str or None
        Clean height value (e.g. '3', '1-5'), if available.
    storey_height : float
        Storey height in meters used for 'H', 'HEX', 'HBET'.

    Returns
    -------
    (min_height, max_height, mid_height) : tuple of float or None
        Heights in meters, or (None, None, None) if nothing could be parsed.
    """
    ht = height_type
    raw = height
    val = height_value

    # Decide which string to parse. height_value is usually cleaner.
    src = val or raw
    if src is not None:
        src = strip_height_prefix(src)

    # 1) HHT: explicit height in meters
    if ht == "HHT":
        if src:
            try:
                h = float(src)
                return h, h, h
            except ValueError:
                pass

    # 2) No type, but we still have a number → treat as meters
    if ht is None and src:
        try:
            h = float(src)
            return h, h, h
        except ValueError:
            pass

    # 3) H or HEX: number of storeys → convert storeys to meters
    if ht in ("H", "HEX") and src:
        try:
            stories = int(float(src))  # handles '3' or '3.0'
            h = stories * storey_height
            return h, h, h
        except ValueError:
            pass

    # 4) HBET: range of storeys, e.g. '1-5' or '1,5'
    if ht == "HBET" and src:
        try:
            parts = src.replace(",", "-").split("-")
            if len(parts) == 2:
                a = int(parts[0])
                b = int(parts[1])
                min_s = min(a, b)
                max_s = max(a, b)
                min_h = min_s * storey_height
                max_h = max_s * storey_height
                mid_h = (min_h + max_h) / 2.0
                return min_h, max_h, mid_h
        except ValueError:
            pass

    # If we get here, we couldn't parse the height
    return None, None, None


def compute_uhi_risk(usage: str, height: float, area: float) -> float:
    """
    Compute a simple Urban Heat Island (UHI) risk score.

    UHI_risk = usage_weight * (HEIGHT_FACTOR * height + AREA_FACTOR * area)

    Parameters
    ----------
    usage : str
        Usage label (e.g. 'residential', 'commercial').
    height : float
        Representative height in meters (usually mid_height).
    area : float
        Footprint area in square meters.

    Returns
    -------
    float
        UHI risk score for this building.
    """
    weight = USAGE_WEIGHTS.get(usage, 1.0)
    return weight * (HEIGHT_FACTOR * height + AREA_FACTOR * area)


# ----------------------------------------------------------------------
# Functional pipeline: row -> building dict -> ranking
# ----------------------------------------------------------------------


def row_to_building(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Turn one database row into a "building" dict with all derived attributes.

    Parameters
    ----------
    row : dict
        Row from the database with keys:
        'id', 'occupancy', 'height', 'height_type', 'height_value', 'area'.

    Returns
    -------
    dict
        Building dictionary with keys:
        'id', 'usage', 'area',
        'min_height', 'max_height', 'mid_height', 'uhi_risk'.
    """
    usage = map_occupancy_to_usage(row.get("occupancy"))
    area = float(row["area"])
    storey_height = get_storey_height(usage)

    min_h, max_h, mid_h = parse_heights(
        height_type=row.get("height_type"),
        height=row.get("height"),
        height_value=row.get("height_value"),
        storey_height=storey_height,
    )

    if mid_h is not None:
        uhi = compute_uhi_risk(usage, mid_h, area)
    else:
        uhi = None

    building = {
        "id": row["id"],
        "usage": usage,
        "area": area,
        "min_height": min_h,
        "max_height": max_h,
        "mid_height": mid_h,
        "uhi_risk": uhi,
    }
    return building


def build_buildings(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a list of database rows into building dictionaries.

    Parameters
    ----------
    rows : list of dict
        Raw rows from the database.

    Returns
    -------
    list of dict
        One building dict per input row.
    """
    return [row_to_building(r) for r in rows]


def get_top_n_by_uhi(buildings: List[Dict[str, Any]], n: int = 10) -> List[Dict[str, Any]]:
    """
    Return the top N buildings ordered by UHI risk (highest first).

    Parameters
    ----------
    buildings : list of dict
        List of building dictionaries with 'uhi_risk' values.
    n : int, optional
        Number of buildings to return (default 10).

    Returns
    -------
    list of dict
        Top N buildings with the largest UHI risk.
    """
    buildings_with_risk = [b for b in buildings if b["uhi_risk"] is not None]
    buildings_with_risk.sort(key=lambda x: x["uhi_risk"], reverse=True)
    return buildings_with_risk[:n]


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    """
    Run the whole functional workflow:

    1. Connect to the database.
    2. Make sure the 'public.enschede_building' table exists.
    3. Read building rows from the table.
    4. Turn them into building dicts and compute UHI risk.
    5. Print the top 10 buildings by UHI risk.
    """
    # Database connection settings (adjust to your local setup)
    DB_CONFIG = {
        "host": "localhost",
        "database": "postgres",
        "user": "postgres",
        "password": "postgres", 
        "port": 5432,
    }

    table_name = "public.enschede_building"
    sql_file = "enschede_building.sql"  # SQL file that creates the table

    # 1. Open a single DB connection for everything
    conn = connect_to_db(DB_CONFIG)

    try:
        # 2. Ensure the table exists (create it from SQL if needed)
        ensure_table_from_sql(conn, table_name=table_name, sql_path=sql_file)

        # 3. Fetch raw rows
        rows = fetch_building_rows(
            conn=conn,
            table_name=table_name,
            limit=100000000,
        )

    finally:
        # Close the connection as soon as we're done with DB work
        conn.close()

    # 4. Convert rows → building dicts and compute UHI
    buildings = build_buildings(rows)

    # 5. Take the top 10 highest UHI risk buildings
    top_buildings = get_top_n_by_uhi(buildings, n=10)

    print("Top 10 buildings by UHI risk (functional approach):")
    for b in top_buildings:
        print(
            f"ID={b['id']} | usage={b['usage']} | "
            f"area={b['area']:.1f} m² | mid_h={b['mid_height']} m | "
            f"UHI={b['uhi_risk']:.3f}"
        )


if __name__ == "__main__":
    main()
