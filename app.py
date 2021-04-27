import os
import uuid

from flask import Flask, render_template, request
import werkzeug

from mal_tier_list_bbcode_gen.spreadsheetparser import SpreadsheetParser
from mal_tier_list_bbcode_gen.bbcodegenerator import BBCodeGenerator

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files.get('ods_file')
        original_filename = werkzeug.utils.secure_filename(f.filename)
        filename = '.'.join([str(uuid.uuid4()), 'ods'])
        path = os.path.join('uploads', filename)

        f.save(path)

        parser = SpreadsheetParser(path)
        parser.parse_tiers()

        generator = BBCodeGenerator(parser.settings, parser.tiers)
        generator.generate_bbcode()

        os.remove(path)

        html_preview = generator._generate_html_preview()
        return render_template('result.html', html_preview=html_preview,
                               bbcode=generator.bbcode)

    return render_template('index.html', title='MALTierListApp')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
