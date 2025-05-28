import datetime

import matplotlib
import matplotlib.pyplot as plt
import requests
from flask import Blueprint, Response, send_file

from constants import IMAGES_FOLDER, TEMPERATURE_API_ADDRESS

dashboard = Blueprint("simple_page", __name__, template_folder="templates")
matplotlib.use("agg")


@dashboard.route("/")
def root():
    try:
        response = requests.get(TEMPERATURE_API_ADDRESS + "/streams", timeout=10)
    except requests.exceptions.ConnectionError:
        return Response("Failed to get response from temperature API", 404)
    if response.status_code != 200:
        return Response("Failed to get response from temperature API", 404)

    return_ = []
    image_path = IMAGES_FOLDER / "test.png"
    for stream in response.json():
        body = {
                "stream": stream,
                "datetimeStart": (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat(),
                #"datetimeEnd": datetime.utcnow().isoformat(),
                "minimumItemsPerPage": 1_000_000
            }
        print(body)
        response = requests.post(
            TEMPERATURE_API_ADDRESS
            + "/streams", json=body,
            timeout=30,
        )
        try:
            r_json = response.json()
        except requests.exceptions.JSONDecodeError:
            print(response.content.decode())
            continue
        print(r_json["metadata"])
        data = r_json["data"]
        print(data.keys())
        return_.append(data)
        for key in data.keys():
            if key != "Datetime":
                plt.plot(
                    [
                        datetime.datetime.fromisoformat(datetime_)
                        for datetime_ in data["Datetime"]
                    ],
                    [float(value) for value in data[key]],
                    label=f"{stream}:{key}",
                )
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()

    return send_file(image_path, mimetype="image/png")
