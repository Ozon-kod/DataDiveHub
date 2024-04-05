from flask import Flask, render_template, request,g,jsonify, send_file,redirect
import sqlite3
from bs4 import BeautifulSoup
import csv
import zipfile
import io

app = Flask(__name__,static_folder='static')

DATABASE="divedata2.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def create_table():
    """This method creates the database tables it is mapped by according to .xml files provided"""
    
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS generator (
        id INTEGER PRIMARY KEY,
        name TEXT,
        manufacturer_id TEXT,
        manufacturer_name TEXT,
        version TEXT,
        date_year INTEGER,
        date_month INTEGER,
        date_day INTEGER,
        date_dayofweek INTEGER,
        time_hour INTEGER,
        time_minute INTEGER
    )
''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diver (
            id INTEGER PRIMARY KEY,
            owner_id TEXT,
            personal_firstname TEXT,
            personal_lastname TEXT,
            equipment_divecomputer_id TEXT,
            equipment_divecomputer_name TEXT,
            equipment_divecomputer_model TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS divesite (
            id INTEGER PRIMARY KEY,
            site_name TEXT,
            environment TEXT,
            latitude REAL,
            longitude REAL,
            altitude REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waypoint (
            id INTEGER PRIMARY KEY,
            dive_id TEXT,
            depth REAL,
            divetime REAL,
            temperature REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS informationbeforedive (
            id INTEGER PRIMARY KEY,
            dive_id TEXT,
            datetime TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS informationafterdive (
            id INTEGER PRIMARY KEY,
            dive_id TEXT,
            diveduration REAL,
            greatestdepth REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repetitiongroup (
            id INTEGER PRIMARY KEY,
            dive_id TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dive (
            id TEXT PRIMARY KEY,
            repetitiongroup_id INTEGER,
            FOREIGN KEY (repetitiongroup_id) REFERENCES repetitiongroup(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owner (
            id TEXT PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buddy (
            id TEXT PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gasdefinitions (
            id INTEGER PRIMARY KEY
        )
    ''')
    connection.commit()

def remove_from_db (data):
    connection=get_db()
    cursor=connection.cursor()
    cursor.execute('DELETE FROM dives WHERE rowid= (?)', (data,))
    connection.commit()


@app.route('/')
def index():
    """
        When we navigate to this route it gets data related to graph and map and return to templates
    """
    connection = get_db()
    cursor = connection.cursor()
    create_table()
    cursor.execute("SELECT * FROM waypoint LIMIT 10")
    data_from_db = cursor.fetchall()
    cursor.execute("SELECT * FROM divesite")
    # Fetched the data from database and return to template and in template we will get that data and show it into table
    dive_site_data=cursor.fetchall()
    cursor.execute("SELECT * FROM diver")
    # Fetched the data from database and return to template and in template we will get that data and show it into table
    diver_data=cursor.fetchall()
    cursor.execute("SELECT * FROM generator")
    # Fetched the data from database and return to template and in template we will get that data and show it into table
    generator_data=cursor.fetchall()
    dive_data=[{'id': row[0], 'dive_id': row[1], 'depth': row[2], 'divetime': row[3], 'temperature': row[4]} for row in data_from_db]
    divesite_data = [{'id': row[0], 'site_name': row[1], 'environment': row[2], 'latitude': row[3], 'longitude': row[4], 'altitude': row[5]} for row in dive_site_data]
    dive_user=[{'id': row[0], 'name': row[1], 'manufacuter_id': row[2], 'manufacuter_name': row[3], 'version': row[4], 'date': str(row[7])+"/"+str(row[6])+"/"+str(row[5])+" "+str(row[9])+":"+str(row[10])} for row in generator_data]
    diver_parse_data=[{'id':row[0],'user_type':row[1],'first_name':row[2],'last_name':row[3],'equipment_device_id':row[4],'equipment_device_name':row[5],'equipment_device_model':row[6]} for row in diver_data]
    return render_template('index.html', dive_data=dive_data,dive_site_data=divesite_data,diver_data=diver_parse_data,dive_user=dive_user)


@app.route('/upload', methods=['POST'])
def upload():
    """
        When we hit the upload route it saves the file in uploads folder and also it uses the 
        parse_xml_and insert data function and save it into database
    """
    if 'xmlFile' in request.files:
        xml_file = request.files['xmlFile']
        file_path = 'uploads/' + xml_file.filename
        xml_file.save(file_path)
        create_table()
        
        data=parse_xml_and_insert_data(file_path,DATABASE)

        response_data = {
            'status': 'success',
            'message': 'File uploaded and data saved to the database successfully!'
        }

    else:
        response_data = {
            'status': 'error',
            'message': 'No file provided.'
        }
    return jsonify(response_data)

@app.route('/download', methods=['GET'])
def download():
    """
        When we hit this route then it gets the data from database and pasrse it into the csv and zip it 
    """
    try:
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM waypoint ")
        waypoint_data = cursor.fetchall()
        cursor.execute("SELECT * FROM divesite")
        divesite_data=cursor.fetchall()
        cursor.execute("SELECT * FROM diver")
        diver_data=cursor.fetchall()
        cursor.execute("SELECT * FROM generator")
        generator_data=cursor.fetchall()
        cursor.execute("SELECT * FROM informationafterdive")
        infoafterdive_data=cursor.fetchall()
        # Fetching data from database
        files = []
        # Converting data into CSV
        for data, table_name in [(waypoint_data, 'waypoint'), (divesite_data, 'divesite'),
                                 (diver_data, 'diver'), (generator_data, 'generator'),
                                 (infoafterdive_data, 'informationafterdive')]:
            csv_data = io.StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow([i[0] for i in cursor.description])  
            csv_writer.writerows(data)
            csv_data.seek(0)
            files.append((csv_data, f'{table_name}.csv'))
        # Zipping the data
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for csv_data, filename in files:
                zip_file.writestr(filename, csv_data.getvalue())

        zip_buffer.seek(0)
        # Downloading the data.
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='dive_data.zip'
        )
    except Exception as e:
        return str(e)
    

def parse_xml_and_insert_data(file_path, db_file):
    """
        What this function does is that it parse the data and insert it into database accordingly
    """
    try:
        with open(file_path, 'r') as f:
            data = f.read()
        
        bs_data = BeautifulSoup(data, 'xml') 
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # Getting the data from xml file and storing it into databse
        generator = bs_data.find("generator")
        generator_data = (
            None,
            generator.find("name").get_text(strip=True) if generator else "Unknown",
            generator.find("manufacturer").get("id") if generator else "Unknown",
            generator.find("manufacturer").find("name").get_text(strip=True) if generator else "Unknown",
            generator.find("version").get_text(strip=True) if generator else "Unknown",
            generator.find("date").find("year").get_text(strip=True) if generator else "Unknown",
            generator.find("date").find("month").get_text(strip=True) if generator else "Unknown",
            generator.find("date").find("day").get_text(strip=True) if generator else "Unknown",
            generator.find("date").find("dayofweek").get_text(strip=True) if generator else "Unknown",
            generator.find("time").find("hour").get_text(strip=True) if generator else "Unknown",
            generator.find("time").find("minute").get_text(strip=True) if generator else "Unknown"
        )
        cursor.execute('''
            INSERT INTO generator (id, name, manufacturer_id, manufacturer_name, version, date_year, date_month, date_day, date_dayofweek, time_hour, time_minute)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', generator_data)
        
        diver = bs_data.find("diver")
        diver_data = (
            None,
            diver.find("owner").get("id"),
            diver.find("personal").find("firstname").get_text(strip=True) if diver.find("personal").find("firstname") else "Unknown",
            diver.find("personal").find("lastname").get_text(strip=True) if diver.find("personal").find("lastname") else "Unknown",
            diver.find("equipment").find("divecomputer").get("id"),
            diver.find("equipment").find("divecomputer").find("name").get_text(strip=True),
            diver.find("equipment").find("divecomputer").find("model").get_text(strip=True)
        )
        cursor.execute('''
            INSERT INTO diver (id, owner_id, personal_firstname, personal_lastname, equipment_divecomputer_id, equipment_divecomputer_name, equipment_divecomputer_model)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', diver_data)
        
        divesite = bs_data.find("divesite")
        divesite_data = (
            None,
            divesite.find("name").get_text(strip=True),
            divesite.find("environment").get_text(strip=True),
            float(divesite.find("geography").find("latitude").get_text(strip=True)),
            float(divesite.find("geography").find("longitude").get_text(strip=True)),
            float(divesite.find("geography").find("altitude").get_text(strip=True))
        )
        cursor.execute('''
            INSERT INTO divesite (id, site_name, environment, latitude, longitude, altitude)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', divesite_data)
        
        repetitiongroup = bs_data.find("repetitiongroup")
        dive = repetitiongroup.find("dive")
        for waypoint in dive.find_all("waypoint"):
            waypoint_data = (
                None,
                repetitiongroup.get("id"),
                float(waypoint.find("depth").get_text(strip=True)),
                float(waypoint.find("divetime").get_text(strip=True)),
                float(waypoint.find("temperature").get_text(strip=True))
            )
            cursor.execute('''
                INSERT INTO waypoint (id, dive_id, depth, divetime, temperature)
                VALUES (?, ?, ?, ?, ?)
            ''', waypoint_data)
        
        informationafterdive = dive.find("informationafterdive")
        informationafterdive_data = (
            None,
            repetitiongroup.get("id"),
            float(informationafterdive.find("diveduration").get_text(strip=True)),
            float(informationafterdive.find("greatestdepth").get_text(strip=True))
        )
        cursor.execute('''
            INSERT INTO informationafterdive (id, dive_id, diveduration, greatestdepth)
            VALUES (?, ?, ?, ?)
        ''', informationafterdive_data)
        
        conn.commit()
        conn.close()
        
        print("Data inserted successfully!")
    except Exception as e:
        print(f"Error parsing XML and inserting data: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)