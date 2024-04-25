import requests, re
from flask import Flask, render_template, jsonify, request
import subprocess
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)

# eXist-db connection settings
EXIST_DB_URL = 'http://localhost:8080/exist/rest'
EXIST_DB_USER = 'admin' #cahnge for your own (admin default)
EXIST_DB_PASSWORD = 'hej' #change for your own password (admin default)

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
    response = requests.get(f'{EXIST_DB_URL}/db', params=params, auth=auth)
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
    # Regular expression to extract numbers between specified tags
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
    XqueryGetDiveComputer = f'''
    let $doc := db:open("dives", "{selected_filename}")
    return $doc//diver/owner/equipment/divecomputer/model/text()
    '''
    results = execute_query(XqueryGetDiveComputer)
    if results:
        return jsonify(results.split('\r\n')[0])
    else:
        return jsonify("Computer not found")

# Request for getting the duration for a file
@app.route('/get-duration', methods=['POST'])
def fetch_duration():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDuration = f'''
    let $doc := db:open("dives", "{selected_filename}")
    return $doc//informationafterdive/diveduration/text()
    '''
    results = execute_query(XqueryGetDuration)
    durations = [float(duration) for duration in results.split()]
    return jsonify(durations[0])

# Request for getting the max depth of a file
@app.route('/get-max-depth', methods=['POST'])
def fetch_max_depth():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetGreatestDepth = f'''
    let $fileName := "{selected_filename}"
    let $doc := db:open("dives", $fileName)
    return $doc//informationafterdive/greatestdepth/text()
    '''
    results = execute_query(XqueryGetGreatestDepth)
    depths = [float(depth) for depth in results.split()]
    return jsonify(depths[0])

# Request for getting the files date
@app.route('/get-date', methods=['POST'])
def fetch_date():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDate = f'''
    let $fileName := "{selected_filename}"
    for $file in collection("dives")
    where base-uri($file) = '/dives/{selected_filename}'
    let $year := $file//generator//date/year
    let $month := if (string-length($file//generator//date/month) = 1) then concat("0", $file//generator//date/month) else string($file//generator//date/month)
    let $day := if (string-length($file//generator//date/day) = 1) then concat("0", $file//generator//date/day) else string($file//generator//date/day)
    return concat($year, '-', $month, '-', $day)
    '''
    results = execute_query(XqueryGetDate)
    if results:
        return jsonify(results.split()[0])
    else:
        return jsonify("Date not found")

# Waypoints below, to create graph, routes for depth, time and temp.
@app.route('/dive-depth', methods=['POST'])
def fetch_wDepth():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDiveDepth = f'''
    let $fileName := "{selected_filename}"
    let $doc := db:open("dives", $fileName)
    return $doc//profiledata/repetitiongroup/dive/samples/waypoint/depth/text()
    '''
    results = execute_query(XqueryGetDiveDepth)
    return jsonify(results.split())

@app.route('/dive-time', methods=['POST'])
def fetch_wDiveTime():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDiveTime = f'''
    let $fileName := "{selected_filename}"
    let $doc := db:open("dives", $fileName)
    return $doc//profiledata/repetitiongroup/dive/samples/waypoint/divetime/text()
    '''
    results = execute_query(XqueryGetDiveTime)
    return jsonify(results.split())

@app.route('/dive-temperature', methods=['POST'])
def fetch_wDiveTemp():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDiveTemp = f'''
    let $fileName := "{selected_filename}"
    let $doc := db:open("dives", $fileName)
    return $doc//profiledata/repetitiongroup/dive/samples/waypoint/temperature/text()
    '''
    results = execute_query(XqueryGetDiveTemp)
    return jsonify(results.split())


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

def process_garmin_file(file):
    input_filepath = os.path.join("testupload", secure_filename(file.filename))
    output_filepath = os.path.join("testupload", secure_filename(file.filename.replace('.fit', '.xml')))
    open(output_filepath, 'a').close()

    file.save(input_filepath)

    command = ['python', 'konvert/Fit2UDDF.py', '-i', input_filepath, '-o', output_filepath]
    try:
        subprocess.run(command, check=True)
        with open(output_filepath, 'rb') as f:
            xml_data = f.read()
        os.remove(input_filepath)  # Optional: remove the original .fit file
        os.remove(output_filepath)  # Optional: remove the processed .xml file
        return xml_data, None
    except subprocess.CalledProcessError as e:
        return None, f"Error processing file: {e}"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'xmlFile' not in request.files:
        return jsonify(message='No file part'), 400
    file = request.files['xmlFile']
    dive_computer = request.form.get('diveComputer', '')
    
    if file.filename == '':
        return jsonify(message='No selected file'), 400

    if dive_computer == 'computer2':  # Garmin
        if not file.filename.endswith('.fit'):
            return jsonify(message='Invalid file format, please upload a FIT file for Garmin'), 400
        xml_data, error = process_garmin_file(file)
        if error:
            return jsonify(message=error), 500
    else:
        if not file.filename.endswith('.xml'):
            return jsonify(message='Invalid file format, please upload an XML file'), 400
        xml_data = file.read()

    filename = secure_filename(file.filename)
    success, message = add_xml_data_to_database("dives", filename.replace('.fit', '.xml'), xml_data)

    if success:
        return jsonify(message=message), 200
    else:
        return jsonify(message=message), 500

    


if __name__ == '__main__':
    app.run(debug=True)
