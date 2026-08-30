import sys, os
from sqlalchemy import text
from app.db.session import SessionLocal

db = SessionLocal()

s1 = db.execute(text("SELECT id, name FROM sites WHERE name LIKE '%Riverside Mall%'")).fetchone()
s2 = db.execute(text("SELECT id, name FROM sites WHERE name LIKE '%Coastal Residency%'")).fetchone()

if s1 and s2:
    id_riv = s1[0]
    id_cst = s2[0]

    db.execute(text(f"UPDATE sites SET name='TEMP' WHERE id={id_riv}"))
    db.execute(text(f"UPDATE sites SET name='Riverside Mall' WHERE id={id_cst}"))
    db.execute(text(f"UPDATE sites SET name='Coastal Residency' WHERE id={id_riv}"))

    tables = [
        ('projects', 'name'),
        ('projects', 'description'),
        ('alerts', 'title'),
        ('alerts', 'description'),
        ('notifications', 'title'),
        ('notifications', 'message'),
        ('inventory_transactions', 'reference'),
        ('material_requests', 'justification'),
    ]
    for t, c in tables:
        db.execute(text(f"UPDATE {t} SET {c} = REPLACE({c}, 'Riverside', 'TEMP_RIV') WHERE {c} IS NOT NULL"))
        db.execute(text(f"UPDATE {t} SET {c} = REPLACE({c}, 'Coastal', 'Riverside') WHERE {c} IS NOT NULL"))
        db.execute(text(f"UPDATE {t} SET {c} = REPLACE({c}, 'TEMP_RIV', 'Coastal') WHERE {c} IS NOT NULL"))

    db.commit()
    print('Successfully swapped Riverside Mall and Coastal Residency in DB.')
else:
    print('Sites not found!')