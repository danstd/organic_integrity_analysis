#from integrity_app.app import app as application
 
#if __name__ == "__main__":
#        app.run()

import sys

# add project directory to the sys.path
project_home = '/application/integrity_app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# import flask app but need to call it "application" for WSGI to work
from integrity_app.app import app as application  # noqa
