from flask import Flask, render_template, jsonify, request
from BaseXClient import BaseXClient

app = Flask(__name__)

# XQuery queries - used for retrieving the whole collection or show all files
XqueryGetFileName = '''
    for $file in db:list("dives")
    return $file
'''

XqueryGetDiveName = """
    for $file in collection("dives")
    return $file//divesite/site/name/text()
"""

XqueryGetDiveCoordinatesLatitude = """
    for $file in collection("dives")
    return $file//divesite/site/geography/latitude/text()
"""

XqueryGetDiveCoordinatesLongitude = """
    for $file in collection("dives")
    return $file//divesite/site/geography/longitude/text()
"""

#Basex connection, later change into public once dockered. But if you're running on your own computer cahnge the username aswell as admin
#because these are my current settings. 
app.config['BASEX_CONNECTION'] = {
    'host': 'localhost',
    'port': 1984,
    'username': 'admin',
    'password': '123'
}

#Creating a session for each request, helped with running multiple queries
def create_session():
    connection = app.config['BASEX_CONNECTION']
    session = BaseXClient.Session(connection['host'], connection['port'], connection['username'], connection['password'])
    return session


def close_session(session):
    session.close()

#Executes query, creates, and closes session
def execute_query(query):
    session = create_session()
    result = session.query(query).execute()
    close_session(session)
    return result

#Starter for choosing template html file
@app.route('/')
def start():
    return render_template("upload.html")

#Return latitude
@app.route('/get-latitude')
def get_latitude():
    results=execute_query(XqueryGetDiveCoordinatesLatitude)
    return jsonify(results)

#Return longitude
@app.route('/get-longitude')
def get_longitude():
    results=execute_query(XqueryGetDiveCoordinatesLongitude)
    return jsonify(results)

# Return file list
@app.route('/get-file-list')
def get_file_list():
    results = execute_query(XqueryGetFileName)
    return jsonify(results)


# Return dive names list
@app.route('/get-dive-name')
def get_file_name():
    results = execute_query(XqueryGetDiveName)
    return jsonify(results)

#Functions below are for specific files choosen from the dive list, they all create a new session and closes it
# Request for getting specific file diving computer
@app.route('/get-dive-computer', methods=['POST'])
def fetch_dive_computer():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDiveComputer = f"""
    let $doc := db:open("dives", '{selected_filename}')
    return $doc//diver/owner/equipment/divecomputer/model/text()
    """
    results = execute_query(XqueryGetDiveComputer)
    if results:
        computer_makes = results.split('\r\n')
        return jsonify(computer_makes[0])
    else:
        return jsonify("Computer not found")


# Request for getting the duration for a file
@app.route('/get-duration', methods=['POST'])
def fetch_duration():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetDuration = f"""
    let $doc := db:open("dives", '{selected_filename}')
    return $doc//informationafterdive/diveduration/text()
    """
    results = execute_query(XqueryGetDuration)
    durations = [float(duration) for duration in results.split()]
    return jsonify(durations[0])


# Request for getting the max depth of a file
@app.route('/get-max-depth', methods=['POST'])
def fetch_max_depth():
    data = request.get_json()
    selected_filename = data['fileName']
    XqueryGetGreatestDepth = f"""
    let $fileName := '{selected_filename}'
    let $doc := db:open("dives", $fileName)
    return $doc//informationafterdive/greatestdepth/text()
    """
    results = execute_query(XqueryGetGreatestDepth)
    depths = [float(depth) for depth in results.split()]
    return jsonify(depths[0])


# Request for getting the files date
@app.route('/get-date', methods=['POST'])
def fetch_date():
    data = request.get_json()
    selected_filename = data['fileName']
    #Using f string to choose what file
    XqueryGetDate = f'''    
    let $fileName := '{selected_filename}'
    for $file in collection("dives")
    where base-uri($file) = '/dives/{selected_filename}'
    let $year := $file//generator//date/year
    let $month := if (string-length($file//generator//date/month) = 1) then concat("0", $file//generator//date/month) else string($file//generator//date/month)
    let $day := if (string-length($file//generator//date/day) = 1) then concat("0", $file//generator//date/day) else string($file//generator//date/day)
    return concat($year, '-', $month, '-', $day)
    '''
    results = execute_query(XqueryGetDate)
    if results:
        dates = results.split()
        return jsonify(dates[0])
    else:
        return jsonify("Date not found")

#Waypoints below, to create graph, routes for depth, time and temp.
@app.route('/dive-depth', methods=['POST'])
def fetch_wDepth():
    data = request.get_json()
    selected_filename = data['fileName']
    #Using f string to choose what file
    XqueryGetDiveDepth = f"""  
    let $fileName := '{selected_filename}'
    let $doc := db:open("dives", $fileName)
    return $doc//profiledata/repetitiongroup/dive/samples/waypoint/depth/text()
    """
    results = execute_query(XqueryGetDiveDepth)
    if results:
        depths = results.split()
        return jsonify(depths)
    else:
        return jsonify("No depths found (wp)")
    
@app.route('/dive-time', methods=['POST'])
def fetch_wDiveTime():
    data = request.get_json()
    selected_filename = data['fileName']
    #Using f string to choose what file
    XqueryGetDiveTime = f"""  
    let $fileName := '{selected_filename}'
    let $doc := db:open("dives", $fileName)
    return $doc//profiledata/repetitiongroup/dive/samples/waypoint/divetime/text()
    """
    results = execute_query(XqueryGetDiveTime)
    if results:
        times = results.split()
        return jsonify(times)
    else:
        return jsonify("No times found (wp)")

@app.route('/dive-temperature', methods=['POST'])
def fetch_wDiveTemp():
    data = request.get_json()
    selected_filename = data['fileName']
    #Using f string to choose what file
    XqueryGetDiveTemp = f"""  
    let $fileName := '{selected_filename}'
    let $doc := db:open("dives", $fileName)
    return $doc//profiledata/repetitiongroup/dive/samples/waypoint/temperature/text()
    """
    results = execute_query(XqueryGetDiveTemp)
    if results:
        temps = results.split()
        return jsonify(temps)
    else:
        return jsonify("No temps found (wp)")


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


# Function to add XML data to the database using db commands
def add_xml_data_to_database(database_name, document_name, xml_data):
    try:
        # Open the existing database or create a new one if it doesn't exist
        session = create_session()
        session.execute("OPEN " + database_name)
        # Add the XML data to the database with its own path
        session.add(document_name, xml_data.decode())  # Convert bytes to string using decode()
        close_session(session)
        return True, "File added to the database successfully"
    except Exception as e:
        return False, "Error adding file to the database: " + str(e)


if __name__ == '__main__':
    app.run(debug=True)
