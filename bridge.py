import os
import requests

from flask import Flask, request, make_response, json
from flask_caching import Cache

root_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
cache = Cache(
    app, config={"CACHE_TYPE": "filesystem", "CACHE_DIR": root_dir + "/cache/"}
)


def full_path_cache_key():
    return request.full_path


def json_response(json_body, status=200):
    return make_response(
        (json.jsonify(json_body), status, {"Content-Type": "application/json"})
    )


@app.route("/")
def index():
    """
    Index page
    Will not use a templates engine for this, sorry
    """
    return """
    <!DOCTYPE html>
    <html><body>
    <h1><a href="https://datastro.eu">Datastro</a> bridges</h1>
    <p>For APIs incompatible with OpenDataSoft supported data models.</p>
    <ul>
        <li>
            <a href="/fireball.api">Fireballs API</a>: same usage, parameters &
            fields as the <a href="https://ssd-api.jpl.nasa.gov/doc/fireball.html">
            official API</a> but with data in JSON dicts instead of list of list
            of fields values with labels apart.
        </li>
    </ul>
    </body></html>
    """


@app.route("/fireball.api")
@cache.cached(timeout=3600, key_prefix=full_path_cache_key)
def fireballs():
    """
    Converts the NASA fireballs API results to a list of dicts.

    The NASA fireballs API returns apart a list of fields and a list of lines.
    This route converts this format to a more exploitable list or key: value dicts.
    """
    r = requests.get("https://ssd-api.jpl.nasa.gov" + request.full_path)

    if not r.ok:
        return json_response(r.json(), r.status_code)

    nasa = r.json()
    converted = []

    for line in nasa["data"]:
        converted.append(dict(zip(nasa["fields"], line)))

    comment = None
    if nasa["signature"]["version"] != "1.0":
        comment = f"Warning: data may be erroneous because the API version has changed (is {nasa['signature']['version']}, but this converter targets 1.0)."

    return json_response(
        {
            "signature": nasa["signature"],
            "count": nasa["count"],
            "comment": comment,
            "data": converted,
        }
    )
