"""
Practical 3 – Data sources
Author: David Alfonso Reyes
Student number: 3598535
"""

# Import libraries
import os
import requests
import geopandas as gpd
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd


def wfs_to_file(base_url: str, layer_name: str, out_path: str, out_format: str, crs: str) -> None:
    """
    Download a WFS layer and save it as a local file.

    This function sends a WFS GetFeature request for a given layer and CRS,
    and writes the response directly to disk .

    Parameters
    ----------
    base_url : str
        Base URL of the WFS service.
    layer_name : str
        Name of the layer to request.
    out_path : str
        Path where the downloaded file will be stored.
    out_format : str
        Output format suffix (e.g. 'json' for GeoJSON).
    crs : str
        Target CRS in the form 'EPSG:XXXX'.
    """
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": layer_name,
        "outputFormat": f"application/{out_format}",
        "srsName": f"urn:ogc:def:crs:{crs.replace(':', '::')}",
    }

    print(f"Requesting WFS {layer_name} ...")
    r = requests.get(base_url, params=params)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(r.content)

    print(f"Saved WFS layer {layer_name} to {out_path}")


def gdf_to_postgis(gdf, conn, table_name, schema="public"):
    """
    Save a GeoDataFrame into a PostGIS table using psycopg2.

    The function:
    - drops the target table if it already exists,
    - creates a new table based on the GeoDataFrame schema,
    - writes all rows, including the geometry column.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame to write to the database. Must have a geometry column.
    conn : psycopg2.extensions.connection
        Open connection to the PostgreSQL/PostGIS database.
    table_name : str
        Name of the table to create or replace.
    schema : str, optional
        Database schema where the table will live (default: 'public').
    """

    def dtype_to_pg(dtype):
        """
        Convert a pandas/NumPy dtype to a simple PostgreSQL type.

        Parameters
        ----------
        dtype : pandas or NumPy dtype
            Data type of a DataFrame column.

        Returns
        -------
        str
            PostgreSQL type name (e.g. BIGINT, DOUBLE PRECISION, TEXT).
        """
        if pd.api.types.is_integer_dtype(dtype):
            return "BIGINT"
        if pd.api.types.is_float_dtype(dtype):
            return "DOUBLE PRECISION"
        if pd.api.types.is_bool_dtype(dtype):
            return "BOOLEAN"
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "TIMESTAMP"
        return "TEXT"   # fallback for anything else

    if gdf.empty:
        raise ValueError("GeoDataFrame is empty; nothing to write.")

    geom_col = gdf.geometry.name
    non_geom = [c for c in gdf.columns if c != geom_col]

    # Try to guess geometry type and SRID from the GeoDataFrame
    first_geom = gdf.geometry.iloc[0]
    geom_type = first_geom.geom_type.upper() if first_geom else "GEOMETRY"
    srid = gdf.crs.to_epsg() if gdf.crs else None

    cur = conn.cursor()

    # Drop existing table so we always start clean
    cur.execute(f"DROP TABLE IF EXISTS {schema}.{table_name};")

    # Build column definitions for the non-geometry attributes
    col_defs = [
        f'"{c}" {dtype_to_pg(gdf[c].dtype)}'
        for c in non_geom
    ]

    # Add geometry column definition (with SRID if available)
    if srid:
        geom_def = f'"{geom_col}" geometry({geom_type},{srid})'
    else:
        geom_def = f'"{geom_col}" geometry({geom_type})'

    create_sql = f"""
        CREATE TABLE {schema}.{table_name} (
            {", ".join(col_defs + [geom_def])}
        );
    """
    cur.execute(create_sql)

    # Prepare rows for bulk insert
    rows = []
    for _, row in gdf.iterrows():
        attrs = [row[c] for c in non_geom]
        geom = row[geom_col]
        geom_hex = geom.wkb_hex if geom is not None else None
        rows.append(tuple(attrs + [geom_hex]))

    # Build INSERT statement
    cols_sql = ", ".join([f'"{c}"' for c in non_geom] + [geom_col])
    insert_sql = f"INSERT INTO {schema}.{table_name} ({cols_sql}) VALUES %s"

    # Use SRID-aware insert if we know the SRID
    if srid:
        template = "(" + ", ".join(["%s"] * len(non_geom)) + \
                   f", ST_SetSRID(ST_GeomFromWKB(decode(%s, 'hex')), {srid}))"
    else:
        template = "(" + ", ".join(["%s"] * len(non_geom)) + \
                   ", ST_GeomFromWKB(decode(%s, 'hex')))"""

    execute_values(cur, insert_sql, rows, template=template)

    conn.commit()
    cur.close()
    print(f"Inserted {len(rows)} rows into {schema}.{table_name}")


def main():
    """
    Workflow for Practical 3.

    Steps:
    1. Download municipal boundaries and population data from WFS (EPSG:28992).
    2. Load the greenery dataset from a local GeoPackage.
    3. Store all datasets in a PostGIS database.
    4. Run SQL queries to:
       - get the population of Rotterdam,
       - get total/male/female population for Zuid-Holland,
       - compute a greenery index per municipality,
       - find the municipalities with the lowest and highest greenery.
    """
    # Target CRS for all WFS downloads (Dutch RD New)
    TARGET_CRS = "EPSG:28992"

    # Folder where all downloaded/processed files are stored
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)

    # Local file paths
    MUNICIPAL_GEOJSON = os.path.join(DATA_DIR, "municipal_boundaries.geojson")
    POP_GEOJSON = os.path.join(DATA_DIR, "popdensitylau.geojson")
    GREEN_GPKG = os.path.join(DATA_DIR, "groen_buurt.gpkg")

    # WFS endpoints and layer names
    MUNICIPAL_WFS = "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wfs/v1_0"
    MUNICIPAL_LAYER = "bg:Gemeentegebied"

    POP_WFS = "https://service.pdok.nl/cbs/pd/wfs/v1_0"
    POP_LAYER = "pd:pd-nl-lau-2018"

    GREEN_WFS = "https://geodata.zuid-holland.nl/geoserver/samenleving/wfs"
    GREEN_LAYER = "samenleving:GEZONDZH_GROEN_BUURT"

    # Connect to local PostgreSQL/PostGIS instance
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="Alfonsinky1996*",  # <- adjust to your local password if needed
        host="localhost",
        port=5432,
    )

    # 1. Data loading and processing

    # Download municipal boundaries as GeoJSON
    wfs_to_file(
        base_url=MUNICIPAL_WFS,
        layer_name=MUNICIPAL_LAYER,
        out_path=MUNICIPAL_GEOJSON,
        out_format="json",
        crs=TARGET_CRS,
    )

    # Download population per municipality as GeoJSON
    wfs_to_file(
        base_url=POP_WFS,
        layer_name=POP_LAYER,
        out_path=POP_GEOJSON,
        out_format="json",
        crs=TARGET_CRS,
    )

    # Greenery dataset:
    # For this practical, the greenery data is already available as a local
    # GeoPackage ('groen_buurt.gpkg'), so we simply read it and copy it into
    # our working data directory.
    groen_buurt_gdf = gpd.read_file("groen_buurt.gpkg")
    print("CRS for groen_buurt_gdf:", groen_buurt_gdf.crs)
    groen_buurt_gdf.to_file(GREEN_GPKG, driver="GPKG")

    # 2. Data storage (write all three layers into PostGIS)

    # Read the three datasets from disk
    groen_buurt_gdf = gpd.read_file(GREEN_GPKG)
    municipal_boundaries_gdf = gpd.read_file(MUNICIPAL_GEOJSON)
    popdensitylau_gdf = gpd.read_file(POP_GEOJSON)

    # Create/replace tables in the database
    gdf_to_postgis(popdensitylau_gdf, conn, table_name="popdensitylau", schema="public")
    gdf_to_postgis(groen_buurt_gdf, conn, table_name="groen_buurt", schema="public")
    gdf_to_postgis(
        municipal_boundaries_gdf, conn, table_name="municipal_boundaries", schema="public"
    )

    # 3. Data retrieval and reporting

    # a) Population for Rotterdam (total, male, female)
    sql = """
    SELECT
        "PD_NL_LAU_T_OBS_VALUE" AS total_population,
        "PD_NL_LAU_M_OBS_VALUE" AS male_population,
        "PD_NL_LAU_F_OBS_VALUE" AS female_population
    FROM public.popdensitylau
    WHERE "text" = 'Rotterdam';
    """
    Rotterdam_population_df = pd.read_sql(sql, conn)
    print('''a) Retrieve the population for the municipality Rotterdam (look at the field text):
    retrieve the total population, male and female.''')
    print(f'Total population: {Rotterdam_population_df["total_population"][0]}')
    print(f'Male population: {Rotterdam_population_df["male_population"][0]}')
    print(f'Female population: {Rotterdam_population_df["female_population"][0]}')

    # b) Total population (and by gender) for all municipalities in Zuid-Holland
    sql = """
    SELECT
        SUM(CAST(b."PD_NL_LAU_T_OBS_VALUE" AS numeric)) AS total_population,
        SUM(CAST(b."PD_NL_LAU_M_OBS_VALUE" AS numeric)) AS male_population,
        SUM(CAST(b."PD_NL_LAU_F_OBS_VALUE" AS numeric)) AS female_population
    FROM public.municipal_boundaries a
    JOIN public.popdensitylau b
        ON a.naam = b."text"
    WHERE a."ligtInProvincieNaam" = 'Zuid-Holland';
    """
    Zuid_Holland_population_df = pd.read_sql(sql, conn)
    print('''b) Report for all the municipalities in Zuid-Holland, the total population, female and
    male. (Suggestion: use a spatial join)''')
    print(f'Total population: {Zuid_Holland_population_df["total_population"][0]}')
    print(f'Male population: {Zuid_Holland_population_df["male_population"][0]}')
    print(f'Female population: {Zuid_Holland_population_df["female_population"][0]}')

    # c) Average greenery index per municipality (only for Zuid-Holland)
    sql = """
    SELECT
        gemeentenaam AS municipality,
        AVG(percentage_groen) AS avg_greenery_index
    FROM public.groen_buurt
    WHERE gemeentenaam IN (
        SELECT naam
        FROM public.municipal_boundaries
        WHERE "ligtInProvincieNaam" = 'Zuid-Holland'
    )
    GROUP BY gemeentenaam;
    """
    avg_greenery_index_df = pd.read_sql(sql, conn)
    print('''c) The greenery index is reported by neighbourhood, please report a greenery index
    per municipality. You can use mean or median to spatially aggregate the index. The
    greenery index is only available for Zuid-Holland.''')
    print(avg_greenery_index_df)

    # d) Municipality with lowest and highest greenery

    def greenery_query(order: str) -> str:
        """
        Build a query to get the municipality with the lowest or highest
        average greenery index in Zuid-Holland.

        Parameters
        ----------
        order : str
            Sort order: use 'ASC' to get the minimum greenery municipality,
            or 'DESC' to get the maximum greenery municipality.

        Returns
        -------
        str
            SQL query string that returns one row with municipality name
            and its average greenery index.
        """
        return f"""
        WITH greenery AS (
            SELECT 
                gemeentenaam AS municipality,
                AVG(percentage_groen) AS avg_greenery_index
            FROM public.groen_buurt
            WHERE gemeentenaam IN (
                SELECT naam 
                FROM public.municipal_boundaries
                WHERE "ligtInProvincieNaam" = 'Zuid-Holland'
            )
            GROUP BY gemeentenaam
        )
        SELECT municipality, avg_greenery_index
        FROM greenery
        ORDER BY avg_greenery_index {order}
        LIMIT 1;
        """

    min_avg_greenery_index_df = pd.read_sql(greenery_query("ASC"), conn)
    max_avg_greenery_index_df = pd.read_sql(greenery_query("DESC"), conn)

    print("d) Report the municipality with the lower and higher level of greenery.")
    print("Municipality with the lower level of greenery:")
    print(min_avg_greenery_index_df)
    print("Municipality with the higher level of greenery:")
    print(max_avg_greenery_index_df)

    conn.close()


if __name__ == "__main__":
    main()
