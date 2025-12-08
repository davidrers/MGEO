"""
Practical 4 - OOP approach

This script:
- Defines Building classes (residential / commercial / industrial / other)
- Parses different height formats into min / max / mid heights in meters
- Computes a simple Urban Heat Island (UHI) risk score per building
- Connects to PostgreSQL/PostGIS and reads buildings from a given table
- Uses a factory to turn database rows into Building objects

Note: GenAI tools were used for commenting and styling purposes only. 
"""

from typing import Optional, Tuple, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# ----------------------------------------------------------------------
# Constants
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
# A) Building classes
# ----------------------------------------------------------------------


class Building:
    """
    Generic building object.

    It stores:
    - an ID (from the database),
    - a usage category (residential / commercial / industrial / other),
    - the footprint area,
    - min / max / mid height in meters,
    - and the final UHI risk value.
    """

    def __init__(
        self,
        building_id: int,
        usage: str,
        area: float,
        min_height: Optional[float] = None,
        max_height: Optional[float] = None,
        mid_height: Optional[float] = None,
    ) -> None:
        """
        Initialize a generic Building instance.

        Parameters
        ----------
        building_id : int
            Unique identifier of the building (e.g. database ID).
        usage : str
            Usage category (e.g. 'residential', 'commercial', 'industrial', 'other').
        area : float
            Footprint area of the building in square meters.
        min_height : float, optional
            Minimum estimated height of the building in meters.
        max_height : float, optional
            Maximum estimated height of the building in meters.
        mid_height : float, optional
            Midpoint height of the building in meters.
        """
        self.building_id = building_id
        self.usage = usage
        self.area = area
        self.min_height = min_height
        self.max_height = max_height
        self.mid_height = mid_height
        self.uhi_risk: Optional[float] = None

    def get_storey_height(self) -> float:
        """
        Return the typical storey height (in meters) for this building type.

        Returns
        -------
        float
            Height in meters used to convert storeys into meters.
        """
        return OTHER_STOREY_HEIGHT


class ResidentialBuilding(Building):
    """Building subclass for residential buildings."""

    def __init__(self, building_id: int, area: float) -> None:
        """
        Initialize a ResidentialBuilding instance.

        Parameters
        ----------
        building_id : int
            Unique identifier of the building.
        area : float
            Footprint area in square meters.
        """
        super().__init__(building_id, "residential", area)

    def get_storey_height(self) -> float:
        """
        Return the typical storey height for residential buildings.

        Returns
        -------
        float
            Storey height in meters.
        """
        return RESIDENTIAL_STOREY_HEIGHT


class CommercialBuilding(Building):
    """Building subclass for commercial buildings."""

    def __init__(self, building_id: int, area: float) -> None:
        """
        Initialize a CommercialBuilding instance.

        Parameters
        ----------
        building_id : int
            Unique identifier of the building.
        area : float
            Footprint area in square meters.
        """
        super().__init__(building_id, "commercial", area)

    def get_storey_height(self) -> float:
        """
        Return the typical storey height for commercial buildings.

        Returns
        -------
        float
            Storey height in meters.
        """
        return OTHER_STOREY_HEIGHT


class IndustrialBuilding(Building):
    """Building subclass for industrial buildings."""

    def __init__(self, building_id: int, area: float) -> None:
        """
        Initialize an IndustrialBuilding instance.

        Parameters
        ----------
        building_id : int
            Unique identifier of the building.
        area : float
            Footprint area in square meters.
        """
        super().__init__(building_id, "industrial", area)

    def get_storey_height(self) -> float:
        """
        Return the typical storey height for industrial buildings.

        Returns
        -------
        float
            Storey height in meters.
        """
        return OTHER_STOREY_HEIGHT


class OtherBuilding(Building):
    """
    Fallback building subclass for all remaining usage types
    (e.g. government, education, agriculture, unknown…).
    """

    def __init__(self, building_id: int, area: float, usage: str = "other") -> None:
        """
        Initialize an OtherBuilding instance.

        Parameters
        ----------
        building_id : int
            Unique identifier of the building.
        area : float
            Footprint area in square meters.
        usage : str, optional
            Usage label for this building (default 'other').
        """
        super().__init__(building_id, usage, area)

    def get_storey_height(self) -> float:
        """
        Return the typical storey height for 'other' buildings.

        Returns
        -------
        float
            Storey height in meters.
        """
        return OTHER_STOREY_HEIGHT


# ----------------------------------------------------------------------
# B) HeightParser (logic outside Building)
# ----------------------------------------------------------------------


class HeightParser:
    """
    Parse the height information coming from the database.

    We expect:
    - height_type  (e.g. 'H', 'HBET', 'HEX', 'HHT', or None)
    - height       (raw string; may contain prefixes like 'HBET:1-5')
    - height_value (string; usually a cleaner version like '1-5' or '3')

    The parser converts this into:
    - min_height, max_height, mid_height in meters
    """

    def __init__(
        self,
        height_type: Optional[str],
        height: Optional[str],
        height_value: Optional[str],
    ) -> None:
        """
        Initialize a HeightParser instance.

        Parameters
        ----------
        height_type : str or None
            Type of height information (e.g. 'H', 'HBET', 'HEX', 'HHT', or None).
        height : str or None
            Raw height string from the database (may include prefixes).
        height_value : str or None
            Clean height value (e.g. '3', '1-5'), if available.
        """
        self.height_type = height_type
        self.height = height
        self.height_value = height_value

    @staticmethod
    def _strip_prefix(s: str) -> str:
        """
        Remove prefixes like 'HBET:' or 'H:' from a height string.

        Parameters
        ----------
        s : str
            Raw height string with possible prefix.

        Returns
        -------
        str
            Height string without prefix and surrounding spaces.
        """
        if ":" in s:
            s = s.split(":", 1)[1]
        return s.strip()

    def parse_heights(
        self, storey_height: float
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Convert the raw height fields into min / max / mid heights in meters.

        Parameters
        ----------
        storey_height : float
            Storey height in meters used when height is given in storeys.

        Returns
        -------
        (min_height, max_height, mid_height) : tuple of float or None
            Parsed heights in meters, or (None, None, None) if parsing fails.
        """
        ht = self.height_type
        raw = self.height
        val = self.height_value

        # Choose the best source string for numeric parsing.
        # height_value is usually cleaner: '1-5' instead of 'HBET:1-5'.
        src = val or raw
        if src is not None:
            src = self._strip_prefix(src)

        # 1) HHT: explicit height in meters
        if ht == "HHT":
            if src:
                try:
                    h = float(src)
                    return h, h, h
                except ValueError:
                    pass

        # If we do not have a type but we still have a numeric value,
        # assume it is already in meters.
        if ht is None and src:
            try:
                h = float(src)
                return h, h, h
            except ValueError:
                pass

        # 2) H or HEX: number of storeys (convert storeys -> meters)
        if ht in ("H", "HEX") and src:
            try:
                stories = int(float(src))  # handles '3' or '3.0'
                h = stories * storey_height
                return h, h, h
            except ValueError:
                pass

        # 3) HBET: range of storeys, e.g. '1-5' or '1,5'
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

        # 4) If we reach this point, we could not extract usable height info
        return None, None, None


# ----------------------------------------------------------------------
# C) UHI risk
# ----------------------------------------------------------------------


def compute_uhi_risk(usage: str, height: float, area: float) -> float:
    """
    Compute a simple Urban Heat Island (UHI) risk score.

    Formula:
        UHI_risk = usage_weight * (HEIGHT_FACTOR * height + AREA_FACTOR * area)

    Parameters
    ----------
    usage : str
        Usage category of the building (e.g. 'residential', 'commercial').
    height : float
        Representative building height in meters (usually mid_height).
    area : float
        Footprint area of the building in square meters.

    Returns
    -------
    float
        UHI risk score for the building.
    """
    weight = USAGE_WEIGHTS.get(usage, 1.0)
    return weight * (HEIGHT_FACTOR * height + AREA_FACTOR * area)


# ----------------------------------------------------------------------
# D) PgDataLoader – dynamic table name
# ----------------------------------------------------------------------


class PgDataLoader:
    """
    Helper class to connect to PostgreSQL/PostGIS and fetch building rows.
    """

    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 5432,
    ) -> None:
        """
        Initialize a PgDataLoader instance with database connection settings.

        Parameters
        ----------
        host : str
            Hostname or IP address of the PostgreSQL server.
        database : str
            Name of the PostgreSQL database.
        user : str
            Database user name.
        password : str
            Password for the database user.
        port : int, optional
            Port number of the PostgreSQL server (default is 5432).
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port

    def _get_connection(self):
        """
        Create and return a new psycopg2 database connection.

        Returns
        -------
        connection
            psycopg2 connection object to the configured database.
        """
        return psycopg2.connect(
            host=self.host,
            dbname=self.database,
            user=self.user,
            password=self.password,
            port=self.port,
        )

    def ensure_table_from_sql(self, table_name: str, sql_path: str) -> None:
        """
        Create the given table if it does not exist yet by running a SQL file.

        Parameters
        ----------
        table_name : str
            Fully qualified table name, e.g. 'public.enschede_building'.
        sql_path : str
            Path to the SQL file that creates/populates the table
            (e.g. 'enschede_building.sql').
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Check if the table already exists
                cur.execute("SELECT to_regclass(%s);", (table_name,))
                exists = cur.fetchone()[0] is not None

                if exists:
                    # Table already exists -> nothing to do
                    return

                # Read and execute the SQL file to create/populate the table
                with open(sql_path, "r", encoding="utf-8") as f:
                    sql_text = f.read()

                cur.execute(sql_text)
                conn.commit()
        finally:
            conn.close()

    def fetch_building_rows(
        self,
        table_name: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch building rows from the given table.

        Parameters
        ----------
        table_name : str
            Full table name, e.g. 'public.enschede_building'.
        limit : int, optional
            Maximum number of rows to read. If None, all rows are fetched.

        Returns
        -------
        list of dict
            List of rows, each represented as a dictionary with keys:
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

        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if limit is not None:
                    cur.execute(sql, (limit,))
                else:
                    cur.execute(sql)

                for record in cur.fetchall():
                    rows.append(dict(record))
        finally:
            conn.close()

        return rows


# ----------------------------------------------------------------------
# E) BuildingFactory – map occupancy + use HeightParser
# ----------------------------------------------------------------------


def map_occupancy_to_usage(occ: Optional[str]) -> str:
    """
    Map an occupancy code into one of four usage categories.

    Categories:
    - 'residential'
    - 'commercial'
    - 'industrial'
    - 'other'

    Parameters
    ----------
    occ : str or None
        Occupancy code from the database (e.g. 'RES', 'COM1', 'IND2').

    Returns
    -------
    str
        High-level usage category.
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


class BuildingFactory:
    """
    Convert raw database rows into fully populated Building objects.
    """

    @staticmethod
    def create_building_from_row(row: Dict[str, Any]) -> Building:
        """
        Create a Building object (of the right subclass) from one database row.

        Steps:
        - Map occupancy to usage category.
        - Instantiate the appropriate Building subclass.
        - Use HeightParser to compute min / max / mid heights.
        - Compute UHI risk using the mid height.

        Parameters
        ----------
        row : dict
            Single building row from the database, containing:
            'id', 'occupancy', 'height', 'height_type',
            'height_value', and 'area'.

        Returns
        -------
        Building
            Building instance with heights and UHI risk filled (if possible).
        """
        usage = map_occupancy_to_usage(row.get("occupancy"))

        # Choose the appropriate subclass
        area = float(row["area"])
        if usage == "residential":
            b = ResidentialBuilding(building_id=row["id"], area=area)
        elif usage == "commercial":
            b = CommercialBuilding(building_id=row["id"], area=area)
        elif usage == "industrial":
            b = IndustrialBuilding(building_id=row["id"], area=area)
        else:
            b = OtherBuilding(building_id=row["id"], area=area, usage="other")

        # Parse min / max / mid height (in meters)
        parser = HeightParser(
            height_type=row.get("height_type"),
            height=row.get("height"),
            height_value=row.get("height_value"),
        )
        min_h, max_h, mid_h = parser.parse_heights(b.get_storey_height())
        b.min_height = min_h
        b.max_height = max_h
        b.mid_height = mid_h

        # Compute UHI risk (if we have a height)
        if b.mid_height is not None:
            b.uhi_risk = compute_uhi_risk(b.usage, b.mid_height, b.area)

        return b


# ----------------------------------------------------------------------
# F) Main script
# ----------------------------------------------------------------------


def main() -> None:
    """
    Run the complete workflow:

    1. Ensure the target table exists (create it from SQL file if needed).
    2. Connect to the PostgreSQL/PostGIS database.
    3. Read building records from the selected table.
    4. Turn each row into a Building object (with heights and UHI risk).
    5. Sort buildings by UHI risk and print the top 10.
    """
    loader = PgDataLoader(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres", 
        port=5432,
    )

    table_name = "public.enschede_building"
    sql_file = "enschede_building.sql"  # assumes this file is in the same folder as the script

    # 1. Make sure the table exists (if not, create it from the SQL file)
    loader.ensure_table_from_sql(table_name=table_name, sql_path=sql_file)

    # 2. Read all buildings from this table
    rows = loader.fetch_building_rows(
        table_name=table_name,
        limit=100000000,
    )

    # 3–5. Same as before
    buildings: List[Building] = [
        BuildingFactory.create_building_from_row(r) for r in rows
    ]

    buildings_with_risk = [b for b in buildings if b.uhi_risk is not None]
    buildings_with_risk.sort(key=lambda x: x.uhi_risk, reverse=True)

    print("Top 10 buildings by UHI risk:")
    for b in buildings_with_risk[:10]:
        print(
            f"ID={b.building_id} | usage={b.usage} | "
            f"area={b.area:.1f} m² | mid_h={b.mid_height} m | "
            f"UHI={b.uhi_risk:.3f}"
        )


if __name__ == "__main__":
    main()
