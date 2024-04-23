import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# eXist-db connection settings
EXIST_DB_URL = 'http://localhost:8080/exist/rest'
EXIST_DB_USER = 'admin'
EXIST_DB_PASSWORD = '123'

# Example XQuery queries
XqueryGetFileName = 'collection("dives")'
XqueryGetDiveName = 'collection("dives")//divesite/site/name/text()'

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

# Starter for choosing template html file
@app.route('/')
def start():
    return render_template("upload2.html")

# Return latitude
@app.route('/get-latitude')
def get_latitude():
    results = execute_query(XqueryGetDiveCoordinatesLatitude)
    return results

# Return longitude
@app.route('/get-longitude')
def get_longitude():
    results = execute_query(XqueryGetDiveCoordinatesLongitude)
    return results

# Return file list
@app.route('/get-file-list')
def get_file_list():
    results = execute_query(XqueryGetFileName)
    return jsonify(results)

# Return dive names list
@app.route('/get-dive-name')
def get_dive_name():
    results = execute_query(XqueryGetDiveName)
    return jsonify(results)

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


# Function to add XML data to the eXist-db database using REST API
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

# Upload route handler, calls data and adds it using function
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'xmlFile' not in request.files:
        return {'message': 'No file part'}, 400

    file = request.files['xmlFile']
    if file.filename == '':
        return {'message': 'No selected file'}, 400

    if file and file.filename.endswith('.xml'):
        filename = file.filename

        # Call the function to add XML data to the database
        success, message = add_xml_data_to_database("dives", filename, file.read())

        if success:
            return {'message': message}, 200
        else:
            return {'message': message}, 500
    else:
        return {'message': 'Invalid file format, please upload an XML file'}, 400


if __name__ == '__main__':
    app.run(debug=True)
