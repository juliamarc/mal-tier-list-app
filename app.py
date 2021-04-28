import os
import uuid
import warnings

import click
import mal_tier_list_bbcode_gen.exceptions as exceptions

from flask import Flask, render_template, request, send_from_directory
from mal_tier_list_bbcode_gen.tierlistgenerator import TierListGenerator
from waitress import serve
from werkzeug.exceptions import RequestEntityTooLarge


UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024


@app.errorhandler(RequestEntityTooLarge)
def handle_bad_request(e):
    return render_template('index.html',
                           error_info='File too large, max. 4MB'), 413


@app.route('/favicon.ico')
def fav():
    return send_from_directory(app.root_path, 'favicon.ico')


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

            with warnings.catch_warnings(record=True) as w:
                tl_gen = TierListGenerator(stored_filename)
                tl_gen.generate()
                warns = [warn.message for warn in w]
        except (
            exceptions.EntriesPerRowMissingError,
            exceptions.EntriesPerRowNotANumberError,
            exceptions.GoogleDriveSourceError,
            exceptions.HeaderIncompleteError,
            exceptions.InvalidImageSourceError,
            exceptions.InvalidMALURL,
            exceptions.SettingsSheetMissingError,
        ) as e:
            return render_template('index.html', error_info=str(e))
        finally:
            try:
                os.remove(stored_filename)
            except FileNotFoundError:
                pass

        return render_template('result.html', html_preview=tl_gen.html,
                               bbcode=tl_gen.bbcode, warnings=warns)

    return render_template('index.html')


@click.command()
@click.option('--dev', is_flag=True)
def main(dev):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if dev:
        app.run(debug=True)
    else:
        serve(app, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    main()
