import os
import time

from flask import Flask, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

import gangster
import cv2


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}

app = Flask("Gangster Serve")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.urandom(16)


def allowed_file(filename):
    ext = os.path.splitext(filename)[-1].lower()[1:]  # get rid of .
    return ext in ALLOWED_EXTENSIONS



@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # if user does not select file, browser also
        # submit a empty part without filename
        if not file.filename:
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            filename = f"tmp_{int(time.time())}{os.path.splitext(filename)[-1]}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            img = cv2.imread(filepath)
            img = gangster.make_gangster(img)
            cv2.imwrite(filepath, img)

            return redirect(url_for("uploaded_file", filename=filename))

    return """
    <!doctype html>
    <title>Auto Gangster</title>
    <h1>Gangsterfy an image</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)