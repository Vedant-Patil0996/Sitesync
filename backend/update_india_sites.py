import os
import random
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM sites")
    site_ids = [row[0] for row in cur.fetchall()]
    
    for sid in site_ids:
        # India bounding box roughly: lat 8.0 to 35.0, lng 68.0 to 97.0
        lat = round(random.uniform(8.0, 35.0), 4)
        lng = round(random.uniform(68.0, 97.0), 4)
        cur.execute("UPDATE sites SET latitude = %s, longitude = %s WHERE id = %s", (lat, lng, sid))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated {len(site_ids)} sites to Indian coordinates.")
except Exception as e:
    print(f"Error: {e}")
