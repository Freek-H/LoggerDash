"""
Start the Temperature API Flask app.
"""

from temperature_api import app
from temperature_api.api.pagination import delete_expired

if __name__ == "__main__":
    delete_expired()
    app.run(host="0.0.0.0", port=4001, debug=True)
