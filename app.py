from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'xmlFile' in request.files:
        xml_file = request.files['xmlFile']
        xml_file.save('uploads/' + xml_file.filename)
        return 'File uploaded successfully!'
    else:
        return 'No file provided.'

if __name__ == '__main__':
    app.run(debug=True)