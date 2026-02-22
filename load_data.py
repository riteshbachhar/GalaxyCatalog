import csv
import psycopg2

DATA_FILE = "glade_sample.csv"
DB_NAME = "glade_api"


def parse_float(value):
    s = value.strip()
    return float(s) if s and s != "-" else None


def parse_int(value):
    s = value.strip()
    return int(s) if s and s != "-" else None


def parse_str(value):
    s = value.strip()
    return s if s and s != "-" else None


conn = psycopg2.connect(dbname=DB_NAME)
cur = conn.cursor()

with open(DATA_FILE, "r") as f:
    lines = [line for line in f if not line.startswith("#") and line.strip()]

# lines[0] = column headers, lines[1] = units row, lines[2] = separator row
reader = csv.DictReader(lines, delimiter="\t")
next(reader)  # units row
next(reader)  # separator row

count = 0
for row in reader:
    cur.execute(
        """
        INSERT INTO galaxies (
            glade_id, pgc, gwgc, hyperleda, twomass, wisexscos, sdss_dr16q,
            object_type,
            ra, dec,
            redshift_helio, redshift_cmb,
            luminosity_distance, e_luminosity_distance,
            apparent_mag_b, apparent_mag_k,
            stellar_mass, log_bns_rate
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s
        )
        """,
        (
            parse_int(row["GLADE+"]),
            parse_int(row["PGC"]),
            parse_str(row["GWGC"]),
            parse_str(row["HyperLEDA"]),
            parse_str(row["2MASS"]),
            parse_str(row["WISExSCOS"]),
            parse_str(row["SDSS-DR16Q"]),
            parse_str(row["Type"]),
            parse_float(row["RAJ2000"]),
            parse_float(row["DEJ2000"]),
            parse_float(row["zhelio"]),
            parse_float(row["zcmb"]),
            parse_float(row["dL"]),
            parse_float(row["e_dL"]),
            parse_float(row["Bmag"]),
            parse_float(row["Kmag"]),
            parse_float(row["M*"]),
            parse_float(row["logRate"]),
        ),
    )
    count += 1

conn.commit()
cur.close()
conn.close()
print(f"Inserted {count} galaxies")
