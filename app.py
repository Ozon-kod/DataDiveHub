from flask import Flask, render_template, request
from flask import Flask, jsonify
import os
from BaseXClient import BaseXClient

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

# Connect to BaseX server
session = BaseXClient.Session('localhost', 1984, 'admin', 'hej123')

def add_xml_data_to_database(database_name, document_name, xml_data):
    # Connect to BaseX server

    try:
        # Open the existing database or create a new one if it doesn't exist
        session.execute("OPEN " + database_name)

        # Add the XML data to the database with its own name
        session.add(document_name, xml_data)

        return True, "File added to the database successfully"
    except Exception as e:
        return False, "Error adding file to the database: " + str(e)
    finally:
        # Close the session
        session.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'xmlFile' not in request.files:
        return {'message': 'No file part'}, 400

    file = request.files['xmlFile']
    if file.filename == '':
        return {'message': 'No selected file'}, 400

    if file and file.filename.endswith('.xml'):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Read XML data from the file
        with open(file_path, "r") as file:
            xml_data = file.read()

        # Add the XML data to the BaseX database
        success, message = add_xml_data_to_database("db2", filename, xml_data)
        if success:
            os.remove(file_path)  # Remove the uploaded file after adding to the database
            return {'message': message}, 200
        else:
            return {'message': message}, 500
    else:
        return {'message': 'Invalid file format, please upload an XML file'}, 400
    

@app.route('/data', methods=['GET'])
def get_data():
        # Define the XQuery query to retrieve manufacturer names
        query_str = '''
        let $results := collection('db2')//generator//manufacturer//name/text()
        return <results>{$results}</results>
        '''
        # Execute the XQuery query
        query = session.query(query_str)
        result = query.execute()
        # Convert result to JSON format
        data = {'result': result}
        print(data)
        
        return jsonify(data),result



if __name__ == '__main__':
    
    app.run(debug=True)
