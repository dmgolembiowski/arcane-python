from flask import Flask, request, abort, redirect
from l.configuration import config
from l.utils import _parse
from typing import Union, Dict, List
from l.models import Registry as __Registry__

app = Flask(__name__)
Registry = __Registry__.open()

class state_machine:
    
    def __init__(self, uri: str):
        self.uri: str = uri
        self.packet: Union[Dict, None] = None
    
    def __enter__(self) -> None:
        self.packet = _parse(self.uri)
        return self

    def __exit__(self) -> None:
        return self

    def run(self):
        if not packet["func"] == "error":
            return Registry[packet["func"]](**packet)
        else:
            # Return the error generated during __enter__
            return packet["kwargs"][0]

@app.route("/", methods=["POST", "GET", "PUT", "DELETE", "PATCH"])
def dummy_index():
    if request.method not in {"GET"}:
        abort(405, "Request method is not supported")
    else:
        return redirect("https://localhost:443/)

@app.route("/<uri>", methods=["POST", "GET", "PUT", "DELETE", "PATCH"])
def index(uri):
    if request.method in {"DELETE", "PUT", "PATCH"}:
        abort(405, "Request method is not supported")
    else:
        with state_machine(request.path) as bot:
            return bot.run()

if __name__ == "__main__":
    app.run(host=config["api_host"],
        port=config["api_port"],
        debug=True)
