from flask import Flask, render_template, request
from flask import Flask, jsonify
import os
from BaseXClient import BaseXClient

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect to BaseX server
session = BaseXClient.Session('localhost', 1984, 'admin', 'hej123')

@app.route('/')
def index():
    return render_template('index.html')

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
        try:
            session.add(filename, xml_data)
            message = 'File uploaded and added to the database successfully'
            return {'message': message}, 200
        except Exception as e:
            return {'message': 'Error adding file to the database: ' + str(e)}, 500
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
