import os
import uuid

from werkzeug.exceptions import RequestEntityTooLarge
from waitress import serve

from flask import Flask, render_template, request

from mal_tier_list_bbcode_gen.bbcodegenerator import BBCodeGenerator
from mal_tier_list_bbcode_gen.image import GoogleDriveSourceError
from mal_tier_list_bbcode_gen.spreadsheetparser import (
    SpreadsheetParser, EntriesPerRowMissingError, EntriesPerRowNotANumberError,
    HeaderIncompleteError)


UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024


@app.errorhandler(RequestEntityTooLarge)
def handle_bad_request(e):
    return 'bad request!', 413

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files.get('ods_file')
        if not f:
            return render_template('index.html', error_info='No file')
        if f.mimetype != 'application/vnd.oasis.opendocument.spreadsheet':
            return render_template('index.html', error_info='Wrong file type')

        stored_filename = os.path.join(app.config['UPLOAD_FOLDER'],
                                       '.'.join([str(uuid.uuid4()), 'ods']))

        try:
            f.save(stored_filename)

            parser = SpreadsheetParser(stored_filename)
            parser.parse_tiers()

            generator = BBCodeGenerator(parser.settings, parser.tiers)
            generator.generate_bbcode()

            bbcode = generator.bbcode
            html_preview = generator._generate_html_preview()
        except (GoogleDriveSourceError,
                EntriesPerRowMissingError,
                EntriesPerRowNotANumberError,
                HeaderIncompleteError,
                KeyError) as e:
            return render_template('index.html', error_info=str(e))
        finally:
            try:
                os.remove(stored_filename)
            except FileNotFoundError:
                pass

        return render_template('result.html', html_preview=html_preview,
                               bbcode=bbcode)

    return render_template('index.html')


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
    # serve(app, host="127.0.0.1", port=5000)
