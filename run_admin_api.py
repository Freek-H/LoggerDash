"""
Runs the Admin API.
"""

from admin_api import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4444, debug=True)
