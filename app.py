import requests, re
from flask import Flask, render_template, jsonify, request
from flask_session import Session
from flask import session
import subprocess
import os
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET

app = Flask(__name__)
#Session which enables to use lattitude and longitude
app.config['SECRET_KEY'] = 'rnadom'  
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# eXist-db connection settings
EXIST_DB_URL = 'http://localhost:8080/exist/rest'
EXIST_DB_USER = 'admin' #cahnge for your own (admin default)
EXIST_DB_PASSWORD = '123' #change for your own password (admin default)

# Collection xquerys (non file specific) !!! Change all collection names to your own collection name
XqueryGetFileName = """
for $file in collection('/dives') 
return base-uri($file) 
"""

XqueryGetDiveName = """
for $file in collection("dives")
return $file//divesite/site/name
"""

XqueryGetDiveCoordinatesLatitude = """
for $file in collection("dives")
return $file//divesite/site/geography/latitude
"""
XqueryGetDiveCoordinatesLongitude = """
for $file in collection("dives")
return $file//divesite/site/geography/longitude
"""

# Function to execute XQuery queries
def execute_query(query):
    auth = (EXIST_DB_USER, EXIST_DB_PASSWORD)
    params = {'_query': query}
    response = requests.get(f'{EXIST_DB_URL}/db/dives', params=params, auth=auth)
    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_numbers_between_tags(xml_data, tag_name):
    """
    Extracts numbers between specified XML tags from XML data.
    
    Args:
    xml_data: The XML data as a string.
    tag_name: The name of the XML tag to extract numbers from.
    
    Returns:
    list: List of numbers extracted from between specified XML tags.
    """
    # Find the indices of the first and last tag occurrences
    start_tag = '<' + tag_name + '>'
    end_tag = '</' + tag_name + '>'
    start_index = xml_data.find(start_tag)
    end_index = xml_data.rfind(end_tag)
    # Extract the substring containing only specified tags
    tag_data = xml_data[start_index:end_index+len(end_tag)]
    # Regular expression (re) to extract numbers between specified tags
    numbers = re.findall(r'<{}>(.*?)</{}>'.format(tag_name, tag_name), tag_data)
    return numbers

# Starter for choosing template html file , !!!!Choose your own name for the render_Template file
@app.route('/')
def start():
    return render_template("upload.html")

# Return latitude
@app.route('/get-latitude')
def get_latitude():
    results = execute_query(XqueryGetDiveCoordinatesLatitude)
    latitude = extract_numbers_between_tags(results, 'latitude')
    return jsonify(latitude)

# Return longitude
@app.route('/get-longitude')
def get_longitude():
    results = execute_query(XqueryGetDiveCoordinatesLongitude)
    longitude = extract_numbers_between_tags(results, 'longitude')
    return jsonify(longitude)

# Return file list
@app.route('/get-file-list')
def get_file_list():
    results = execute_query(XqueryGetFileName)
    regex = r"\/db\/dives\/([^<]+)\.xml"
    file_names = re.findall(regex, results)
    return jsonify(file_names)

# Return dive names list
@app.route('/get-dive-name')
def get_dive_name():
    results = execute_query(XqueryGetDiveName)
    names = extract_numbers_between_tags(results, 'name')   
    return jsonify(names)

# Request for getting specific file diving computer
@app.route('/get-dive-computer', methods=['POST'])
def fetch_dive_computer():
    data = request.get_json()
    selected_filename = data['fileName']
    index = data['index']
    XqueryGetDiveComputer = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//diver/owner/equipment/divecomputer/model
    '''
    results=execute_query(XqueryGetDiveComputer)
    durations=extract_numbers_between_tags(results, 'model')
    return durations[index]

# Request for getting the duration for a file
@app.route('/get-duration', methods=['POST'])
def fetch_duration():
    data = request.get_json()
    selected_filename = data['fileName']
    index = data['index']
    XqueryGetDuration = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//informationafterdive/diveduration
    '''
    results = execute_query(XqueryGetDuration)
    durations = extract_numbers_between_tags(results, 'diveduration')
    return durations[index]

# Request for getting the max depth of a file
@app.route('/get-max-depth', methods=['POST'])
def fetch_max_depth():
    data = request.get_json()
    selected_filename = data['fileName']
    index = data['index']
    XqueryGetGreatestDepth = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//informationafterdive/greatestdepth
    '''
    results = execute_query(XqueryGetGreatestDepth)
    depths=extract_numbers_between_tags(results, 'greatestdepth')
    result = depths[index]
    return result

# Request for getting the files date
@app.route('/get-date', methods=['POST'])
def fetch_date():
    data = request.get_json()
    selected_filename = data['fileName']
    index = data['index']
    XqueryGetDate = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//generator/date
    '''
    results = execute_query(XqueryGetDate)
    year=extract_numbers_between_tags(results, 'year')
    month=extract_numbers_between_tags(results, 'month')
    day=extract_numbers_between_tags(results, 'day')
    result = "-".join([year[index], month[index], day[index]])
    return result

# Waypoints below, to create graph, routes for depth, time and temp.
@app.route('/dive-depth', methods=['POST'])
def fetch_wDepth():
    data = request.get_json()
    depths = []
    selected_filename = data['fileName']
    XqueryGetDiveDepth = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//samples
    '''
    results = execute_query(XqueryGetDiveDepth)
    matches = re.findall(r'<waypoint>(.*?)</waypoint>', results, re.DOTALL)
    for match in matches: 
        depth_match = re.search(r'<depth>(.*?)</depth>', match, re.DOTALL)
        depths.append(float(depth_match.group(1)))
    return depths 

@app.route('/dive-time', methods=['POST'])
def fetch_wDiveTime():
    data = request.get_json()
    divetime = []
    selected_filename = data['fileName']
    XqueryGetDiveTime = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//samples
    '''
    results = execute_query(XqueryGetDiveTime)
    matches = re.findall(r'<waypoint>(.*?)</waypoint>', results, re.DOTALL)
    for match in matches:
        depth_match = re.search(r'<divetime>(.*?)</divetime>', match, re.DOTALL)
        divetime.append(float(depth_match.group(1)))
    return divetime

@app.route('/dive-temperature', methods=['POST'])
def fetch_wDiveTemp():
    data = request.get_json()
    temperatures = []
    selected_filename = data['fileName']
    XqueryGetDiveTemp = f'''
    for $doc in collection(/db/dives/{selected_filename})
    return $doc//samples
    '''
    results = execute_query(XqueryGetDiveTemp)
    matches = re.findall(r'<waypoint>(.*?)</waypoint>', results, re.DOTALL)
    for match in matches:
        depth_match = re.search(r'<temperature>(.*?)</temperature>', match, re.DOTALL)
        temperatures.append(float(depth_match.group(1)))
    return temperatures

#Add file to database
def add_xml_data_to_database(database_name, document_name, xml_data):
    url = f"{EXIST_DB_URL}/db/{database_name}/{document_name}"
    auth = (EXIST_DB_USER, EXIST_DB_PASSWORD)
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.put(url, auth=auth, data=xml_data, headers=headers)
        response.raise_for_status()
        return True, "File added to the database successfully"
    except requests.exceptions.RequestException as e:
        return False, f"Error adding file to the database: {e}"
    
#Update garmin xml file with coordniates
def update_xml_with_coordinates(filepath, latitude, longitude,name):
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    for divesite in root.findall('.//divesite'):
        site = divesite.find('site')
        name=site.find('name')
        geo = site.find('geography')
        lat_elem = geo.find('latitude')
        long_elem = geo.find('longitude')
        
        if lat_elem is not None:
            lat_elem.text = str(latitude)
        if long_elem is not None:
            long_elem.text = str(longitude)
        if name is not None:
            name.text = str(name)
    
    tree.write(filepath)  # Save changes back to the file

#function for running convertion on garmin fit file
def process_garmin_file(file, latitude, longitude, name):
    input_filepath = os.path.join("testupload", secure_filename(file.filename))
    output_filepath = os.path.join("testupload", secure_filename(file.filename.replace('.fit', '.xml')))
    open(output_filepath, 'a').close()

    file.save(input_filepath)

    command = ['python', 'konvert/Fit2UDDF.py', '-i', input_filepath, '-o', output_filepath]
    try:
        subprocess.run(command, check=True)
        update_xml_with_coordinates(output_filepath, latitude, longitude, name)
        with open(output_filepath, 'rb') as f:
            xml_data = f.read()
        os.remove(input_filepath)  
        os.remove(output_filepath)  
        return xml_data, None
    except subprocess.CalledProcessError as e:
        return None, f"Error processing file: {e}"
    
# Route to receive latitude, longitude and name from frontend
@app.route('/use-coordinates', methods=['POST'])
def use_coordinates():
    data = request.get_json()
    session['latitude'] = data.get('latitude')
    session['longitude'] = data.get('longitude')
    session['name']=data.get('name')

    return jsonify({'message': 'Data stored for future use'})


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'xmlFile' not in request.files:
        return jsonify(message='No file part'), 400
    file = request.files['xmlFile']
    dive_computer = request.form.get('diveComputer', '')

    # Retrieve coordinates from the session
    latitude = session.get('latitude')
    longitude = session.get('longitude')
    name=session.get('name')
    if not latitude or not longitude or not name:
        return jsonify(message='Data not set'), 400
    
    if file.filename == '':
        return jsonify(message='No selected file'), 400

    if dive_computer == 'computer2':  # Garmin
        if not file.filename.endswith('.fit'):
            return jsonify(message='Invalid file format, please upload a FIT file for Garmin'), 400
        xml_data, error = process_garmin_file(file,latitude, longitude, name)
        if error:
            return jsonify(message=error), 500
    else:
        if not file.filename.endswith('.xml'):
            return jsonify(message='Invalid file format, please upload an XML file'), 400
        xml_data = file.read()

    filename = secure_filename(file.filename)
    success, message = add_xml_data_to_database("dives", filename.replace('.fit', '.xml'), xml_data)

    if success:
        session.pop('latitude', None)
        session.pop('longitude', None)
        session.pop('name', None)
        return jsonify(message=message), 200

    else:
        return jsonify(message=message), 500

@app.route('/download', methods=['POST'])
def download_file():
    data = request.get_json()
    selected_filename = data['fileName']
    if not selected_filename.endswith('.xml'):
        selected_filename += '.xml'
    XqueryGetFile = f'''
    let $file := doc('/db/dives/{selected_filename}')
    return $file
    '''
    result=execute_query(XqueryGetFile)
    return result

if __name__ == '__main__':
    app.run(debug=True)
