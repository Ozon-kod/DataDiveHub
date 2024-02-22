import sqlite3
import xml.etree.cElementTree as ET 
from datetime import datetime

# Connect to SQLite database (or create if not exists)
conn = sqlite3.connect('divedata.db')

# Create a cursor object to interact with the database
cursor = conn.cursor()

# Create a table if not exists for diving data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS dives (
        dive_site TEXT,
        location TEXT,
        depth REAL,
        duration INTEGER,
        date TEXT,
        dive_id TEXT,
        latitude, INTEGER,
        longitude, INTEGER,
        altitude, INTEGER 
    )   
''')



# Function to add a new dive
def add_dive(dive_site, location, depth, duration, date):
    cursor.execute('''
        INSERT INTO dives (dive_site, location, depth, duration, date) VALUES (?, ?, ?, ?, ?)
    ''', (dive_site, location, depth, duration, date))
    conn.commit()


# Function to retrieve all dives
def get_all_dives():
    cursor.execute('SELECT * FROM dives')
    dives = cursor.fetchall()
    return dives

#Retrieve all dives with rowid
def get_all_id():
    cursor.execute('SELECT rowid, *FROM dives')
    dives = cursor.fetchall()
    return dives
    

# Retrieve and display all dives
def print_table():
    all_dives = get_all_id()
    print("List of Dives:")
    for dive in all_dives:
        print(dive)

#Fetch one specific dive
def get_dive_by_id(dive_id):
    cursor.execute('SELECT * FROM dives WHERE rowid = (?)',(dive_id, ))
    spec_dive=cursor.fetchone()
    return spec_dive

#Delete dive
def delete_dive(dive_id):
    cursor.execute('DELETE FROM dives WHERE rowid= (?)', (dive_id,))
    conn.commit()
    




print_table()


# Close the cursor and connection
cursor.close()
conn.close()

