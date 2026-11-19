import sys
import os

project_home = "/home/dev1dill2flowers/flo"

if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ["DILL_DATA_DIR"] = "/home/dev1dill2flowers/flo-data"
os.environ["DILL_ADMIN_KEY"] = "BRUce260385"
os.environ["DILL_SECRET_KEY"] = "a-different-long-random-secret"

os.environ["GOOGLE_PLACES_API_KEY"] = "your-private-google-api-key"
os.environ["GOOGLE_PLACE_ID"] = "ChIJTQV8RQGviUgRZUdY1A9JCvg"

from app import app as application

if __name__ == "__main__":
    application.run(debug=True)
