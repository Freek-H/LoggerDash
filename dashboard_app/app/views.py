from datetime import datetime, timedelta

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
        response = requests.get(
            TEMPERATURE_API_ADDRESS
            + f"/stream/{stream}/{datetime.utcnow() - timedelta(minutes=5)}/{datetime.utcnow()}",
            timeout=10,
        )
        data = response.json()
        print(data.keys())
        return_.append(data)
        for key in data.keys():
            if key != "Datetime":
                plt.plot(
                    [
                        datetime.fromisoformat(datetime_)
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
