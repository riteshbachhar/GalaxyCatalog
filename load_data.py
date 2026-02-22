import csv
import psycopg2

conn = psycopg2.connect(dbname="glade_api")
cur = conn.cursor()

with open("glade_sample.csv", "r") as f:
    # Skip comment lines and blank lines
    lines = [line for line in f if not line.startswith("#") and line.strip()]

# Parse TSV — first line is the header, then skip units row and separator row
reader = csv.DictReader(lines, delimiter='\t')
next(reader)  # skip units row (e.g. "deg  deg  Mpc  mag  mag")
next(reader)  # skip separator row (e.g. "------  ------  ...")

count = 0
for row in reader:
    # Handle empty values
    ra = float(row['RAJ2000']) if row['RAJ2000'].strip() else None
    dec = float(row['DEJ2000']) if row['DEJ2000'].strip() else None
    dl = float(row['dL']) if row['dL'].strip() else None
    bmag = float(row['Bmag']) if row['Bmag'].strip() else None
    kmag = float(row['Kmag']) if row['Kmag'].strip() else None
    
    cur.execute("""
        INSERT INTO galaxies (ra, dec, luminosity_distance, apparent_mag_b, apparent_mag_k)
        VALUES (%s, %s, %s, %s, %s)
    """, (ra, dec, dl, bmag, kmag))
    count += 1

conn.commit()
cur.close()
conn.close()
print(f"Inserted {count} galaxies")
