import sqlite3
from bs4 import BeautifulSoup

# Parse the XML file with BeautifulSoup
with open('diver.xml', 'r', encoding='utf-8') as xml_file:
    soup = BeautifulSoup(xml_file, 'xml')

# Create SQLite database and cursor
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS generator (
        name TEXT,
        manufacturer_id TEXT,
        manufacturer_name TEXT,
        version TEXT,
        date_year TEXT,
        date_month INTEGER,
        date_day INTEGER,
        date_dayofweek INTEGER,
        time_hour INTEGER,
        time_minute INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS divecomputer (
        id TEXT,
        name TEXT,
        model TEXT,
        diver_id TEXT,
        FOREIGN KEY (diver_id) REFERENCES diver (id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS diver (
        id TEXT,
        firstname TEXT,
        lastname TEXT,
        owner_id TEXT,
        FOREIGN KEY (owner_id) REFERENCES owner (id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS divesite (
        id TEXT,
        name TEXT,
        environment TEXT,
        latitude REAL,
        longitude REAL,
        altitude REAL
    )
''')

# Insert data into tables using BeautifulSoup
generator = soup.find('generator')
cursor.execute('''
    INSERT INTO generator VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    generator.find('name').text if generator.find('name') is not None else None,
    generator.find('manufacturer')['id'] if generator.find('manufacturer') is not None and 'id' in generator.find('manufacturer').attrs else None,
    generator.find('manufacturer').find('name').text if generator.find('manufacturer').find('name') is not None else None,
    generator.find('version').text if generator.find('version') is not None else None,
    int(generator.find('date').find('year').text) if generator.find('date').find('year') is not None else None,
    int(generator.find('date').find('month').text) if generator.find('date').find('month') is not None else None,
    int(generator.find('date').find('day').text) if generator.find('date').find('day') is not None else None,
    int(generator.find('date').find('dayofweek').text) if generator.find('date').find('dayofweek') is not None else None,
    int(generator.find('time').find('hour').text) if generator.find('time').find('hour') is not None else None,
    int(generator.find('time').find('minute').text) if generator.find('time').find('minute') is not None else None,
    
))

divecomputer = soup.find('divecomputer')
cursor.execute('''
    INSERT INTO divecomputer VALUES (?, ?, ?, ?)
''', (
    divecomputer['id'] if divecomputer is not None and 'id' in divecomputer.attrs else None,
    divecomputer.find('name').text if divecomputer.find('name') is not None else None,
    divecomputer.find('model').text if divecomputer.find('model') is not None else None,
    divecomputer.find('owner')['id'] if divecomputer.find('owner') is not None and 'id' in divecomputer.find('owner').attrs else None,
))

diver = soup.find('diver')
cursor.execute('''
    INSERT INTO diver VALUES (?, ?, ?, ?)
''', (
    diver['id'] if diver is not None and 'id' in diver.attrs else None,
    diver.find('personal').find('firstname').text if diver.find('personal').find('firstname') is not None else None,
    diver.find('personal/lastname').text if diver.find('personal/lastname') is not None else None,
    diver.find('owner')['id'] if diver.find('owner') is not None and 'id' in diver.find('owner').attrs else None,
))

divesite = soup.find('divesite')
cursor.execute('''
    INSERT INTO divesite VALUES (?, ?, ?, ?, ?, ?)
''', (
    divesite.find('site')['id'] if divesite.find('site') is not None and 'id' in divesite.find('site').attrs else None,
    divesite.find('name').text if divesite.find('name') is not None else None,
    divesite.find('environment').text if divesite.find('environment') is not None else None,
    float(divesite.find('geography').find('latitude').text) if divesite.find('geography').find('latitude') is not None else None,
    float(divesite.find('geography').find('longitude').text) if divesite.find('geography').find('longitude') is not None else None,
    float(divesite.find('altitude').text) if divesite.find('altitude') is not None else None,
))

# Commit changes and close connection
conn.commit()
conn.close()
