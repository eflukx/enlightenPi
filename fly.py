from flask import Flask
import sys
app = Flask(__name__)

@app.route("/")
def hello():
    return str(sys.getwindowsversion()[4]) + " ...Hello World!" + str(sys.platform)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)