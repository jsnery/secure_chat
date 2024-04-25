from flask import Flask

app = Flask(__name__)


from app.controllers import default  # noqa: F401 E402
