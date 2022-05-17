import os
import time
import secrets

from flask import (
    Flask,
    request,
    flash,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
    render_template,
    make_response,
)
from werkzeug.utils import secure_filename
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app, Summary

import gangster
import cv2


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

app = Flask("Gangster Serve", static_folder="static")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Limit upload size to 5mb
app.secret_key = secrets.token_urlsafe(32)

# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

# prometheus metrics
s_round_trip = Summary(
    "gangsterify_request_latency_s", "Round trip time to gangsterify an image"
)
s_cv = Summary("gangsterify_cv_time_s", "Compute time to gangsterify an image")
gangster.make_gangster = s_cv.time()(gangster.make_gangster)


def allowed_file(filename):
    ext = os.path.splitext(filename)[-1].lower()[1:]  # get rid of .
    return ext in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/")
@s_round_trip.time()
def upload_file():
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

        filename = f"tmp_{int(1000*time.time())}{os.path.splitext(filename)[-1]}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        img = cv2.imread(filepath)
        n_faces = gangster.make_gangster(img)
        cv2.imwrite(filepath, img)
        res_url = url_for("uploaded_file", filename=filename)
        if n_faces == 0:
            msg = "No faces found"
        elif n_faces == 1:
            msg = "Found 1 face"
        else:
            msg = f"Found {n_faces} faces"

        return render_template("index.html", res_url=res_url, msg=msg)
    return render_template("index.html")


@app.route("/api", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        print("File not in request")
        return jsonify({})

    file = request.files["file"]
    if not file.filename:
        print("No selected file")
        return jsonify({})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        filename = f"tmp_{int(1000*time.time())}{os.path.splitext(filename)[-1]}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        img = cv2.imread(filepath)
        gangster.make_gangster(img)
        cv2.imwrite(filepath, img)

        return jsonify({"url": url_for("uploaded_file", filename=filename)})
    return jsonify({})


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    resp = make_response(send_from_directory(app.config["UPLOAD_FOLDER"], filename))
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


@app.route("/favicon.ico")
@app.route("/robot.txt")
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == "__main__":
    app.run()
