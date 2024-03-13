from flask import Flask, render_template, request,g,jsonify
import sqlite3
from bs4 import BeautifulSoup


app = Flask(__name__)

DATABASE="divedata2.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def create_table():
    # Create a table if not exists
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dives (
        NAME TEXT,
        DATE TEXT,
        SITE_name TEXT
    )
    ''')
    connection.commit()

def insert_data_into_db(data):
    # Insert data into the database
    connection = get_db()
    cursor = connection.cursor()

    # insert_query = 'INSERT INTO your_table (NAME, Manufacturer_id, DATE, TIME, OWNER_id, DIVECOMPUTER_id, DIVECOMPUTER_name, DIVECOMPUTER_model, SITE_id, SITE_name, SITE_enviroment, LATITUDE, LONGITUDE, ALTITUDE INTEGER  ...) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,...);'
    # insert_query='INSERT INTO dives (NAME, DATE, SITE_name) VALUES(?,?,?)'
    cursor.execute('''
                   INSERT INTO dives (NAME, DATE, SITE_name) VALUES(?,?,?)
                   ''',(data[0], data[1],data[2]))
    connection.commit() 

def remove_from_db (data):
    connection=get_db()
    cursor=connection.cursor()
    cursor.execute('DELETE FROM dives WHERE rowid= (?)', (data,))
    connection.commit()

@app.route('/')
def index():
    # Fetch data from the database
    connection = get_db()
    cursor = connection.cursor()
    create_table()
    cursor.execute("SELECT * FROM dives")
    data_from_db = cursor.fetchall()

    # Render the template and pass the data to it
    return render_template('index.html', data=data_from_db)



@app.route('/upload', methods=['POST'])
def upload():
    if 'xmlFile' in request.files:
        xml_file = request.files['xmlFile']
        file_path = 'uploads/' + xml_file.filename
        xml_file.save(file_path)

        # Parse the XML file and extract data
        data = parse_xml(file_path)

        # Create table if not exists
        

        # Insert data into the database
        insert_data_into_db(data)

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
    

def parse_xml(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
    
    bs_data = BeautifulSoup(data, 'xml') 
    bs_name = bs_data.find("name").get_text(strip=True)  # Extract text content
    bs_date = bs_data.find("year").get_text(strip=True)  # Extract text content
    bs_SITE_name = bs_data.find("environment").get_text(strip=True)  # Extract text content

    data = [bs_name, bs_date, bs_SITE_name]
    return data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
