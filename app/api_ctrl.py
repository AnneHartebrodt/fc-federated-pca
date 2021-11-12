import json
import time

from bottle import Bottle, request

from .logic import logic

api_server = Bottle()


# CAREFUL: Do NOT perform any computation-related tasks inside these methods, nor inside functions called from them!
# Otherwise your app does not respond to calls made by the FeatureCloud system quickly enough
# Use the threaded loop in the app_flow function inside the file logic.py instead


@api_server.post("/setup")
def ctrl_setup():
    time.sleep(1)
    print(f"[API] POST /setup", flush=True)
    payload = request.json
    logic.handle_setup(payload["id"], payload["master"], payload["clients"])
    return ""


@api_server.get("/status")
def ctrl_status():
    print(f"[API] GET /status (available={logic.status_available} finished={logic.status_finished})", flush=True)
    return json.dumps({
        "available": logic.status_available,
        "finished": logic.status_finished,
        "message": logic.message,
        "state": logic.workflow_state,
        "progress": logic.progress,
    })


@api_server.route("/data", method="GET")
def ctrl_data_out():
    print(f"[API] GET /data", flush=True)
    return logic.handle_outgoing()


@api_server.route("/data", method="POST")
def ctrl_data_in():
    print(f"[API] POST /data", flush=True)
    logic.handle_incoming(request.body, request.query, request.content_length)
    return ""
