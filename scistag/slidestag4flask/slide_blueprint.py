import time
from flask import Blueprint, Response, request, render_template, abort, jsonify
import base64
from scistag.remotestag import SessionHandler, Session
from scistag.slidestag import SlideApp
from scistag.slidestag.slide_session import SlideSession
from scistag.slidestag.slide_application_manager import SlideAppManager
from scistag.common.flask.flask_common import make_uncacheable

MINIMUM_CAMERA_DATA_SIZE = 100
"The minimum size of a camera data package to be valid"


class SlideStagService(Blueprint):
    """
    The blueprint provides access to SlideStag UI application which can either be access via the web browser
    or any of the clients.
    """

    def __init__(self):
        super().__init__("SlideStag", __name__, template_folder="./templates", static_folder="./static")


slidestag_service = SlideStagService()


@slidestag_service.route("/s4fok")
def get_ok():
    """
    OK check
    :return:
    """
    return "Slidestag for Flask"


def get_session_template(session_id: str, response_format: str, webcam: bool, interactive: bool):
    """
    Returns the session template
    :param session_id: The ID of the new session
    :param response_format: The response format, either "json" or "html"
    :param webcam: Defines if a webcam is required
    :param interactive: Defines if the user interactions shall be sent to the server
    :return:
    """
    if response_format == "json":
        return jsonify({"rootUrl": request.root_url,
                        "singleImageUrl": f"{request.root_url}sessions/{session_id}/screen",
                        "streamUrl": f"{request.root_url}sessions/{session_id}/slideStream",
                        "sessionId": session_id,
                        "supportWebcam": webcam,
                        "supportUserInteraction": interactive})
    else:
        return render_template("slidestag_base.html",
                               slider_root_url=request.root_url,
                               use_mjpeg=True,
                               session_id=session_id,
                               support_webcam=webcam,
                               support_user_interaction=interactive)


@slidestag_service.route("/apps/<app_name>")
def app_entry_point(app_name):
    """
    Initializes an application session
    """
    response_format = request.args.get("format", "html")
    sh = SessionHandler.shared_handler
    session_id = sh.create_session_id()
    app_man = SlideAppManager.shared_app_manager
    if not app_man.app_is_valid(app_name):
        abort(404)
    config = {Session.SESSION_ID: session_id,
              Session.REMOTE_SESSION: True}
    session = app_man.create_session(app_name, config=config)
    config = session.update_config()
    response = get_session_template(session_id, response_format=response_format, webcam=config['permissions']['webcam'],
                                    interactive=config['permissions']['userInput'])
    return response


def create_live_image(session_id: str):
    """
    Creates the next image for the current session
    :param session_id: The session's id
    """
    session: Session = SessionHandler.shared_handler.get_session(session_id)
    if session is None:  # try to fallback to guest session
        session: Session = SessionHandler.shared_handler.get_session_by_guest_id(session_id)
        if session is not None:
            return session.get_guest_data()
    if session is None or not isinstance(session, SlideSession):
        return None
    with session.lock:
        session.handle_used()
        session: SlideSession
        config = {}
        session.handle_main_loop()
        ret = session.render_and_compress(config)
        if session.guest_id is not None:
            session.set_guest_data(ret)
        return ret


@slidestag_service.route("/sessions/<session_id>/screen", methods=['POST', 'GET'])
def get_live_image(session_id: str):
    """
    Returns a multipart response providing images as they are received from the camera
    """
    session: Session = SessionHandler.shared_handler.get_session(session_id)
    if session is None or not isinstance(session, SlideSession):
        guest_session: Session = SessionHandler.shared_handler.get_session_by_guest_id(session_id)
        if guest_session is not None:
            with guest_session:
                response = Response(guest_session.get_guest_data(), content_type="image/jpeg")
            return make_uncacheable(response)
        time.sleep(2.0)
        return Response("Session does not exist", status=404)
    SessionHandler.shared_handler.garbage_collect()
    with session.lock:
        if len(request.data) > 4:
            if request.data.startswith(b'[') or request.data.startswith(b'{'):
                session.set_user_data("clientEvents", request.data)
            else:
                data = request.data
                if len(data) >= MINIMUM_CAMERA_DATA_SIZE:
                    if request.data.startswith(b'data:') and len(request.data):
                        b64_data = request.data.split(bytes(",", "ASCII"))[1]
                        data = base64.b64decode(b64_data)
                    session.set_user_data("camera_00", data)
        using_camera = session.get_needs_camera()
        result_image = create_live_image(session_id)
    response = Response(result_image, content_type="image/jpeg")
    response.headers.set("usingCamera", "yes" if using_camera else "no")
    return make_uncacheable(response)


def live_image_yield(session_id: str):
    """
    Returns a single image's data of a slide
    """
    while True:
        SessionHandler.shared_handler.garbage_collect()
        ret = create_live_image(session_id)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + ret + b'\r\n'


@slidestag_service.route("/sessions/<session_id>/slideStream")
def live_image_stream(session_id):
    """
    Returns an image stream as MotionJpeg or MotionPNG which delivers a continuous stream of still images
    """
    session: Session = SessionHandler.shared_handler.get_session(session_id)
    if session is None:  # try to fallback to guest session
        session: Session = SessionHandler.shared_handler.get_session_by_guest_id(session_id)
    if session is None or not isinstance(session, SlideSession):
        return Response("Session does not exist", status=404)
    return Response(live_image_yield(session_id), mimetype='multipart/x-mixed-replace; boundary=frame')


@slidestag_service.route("/sessions/<session_id>/postUserData/<data_name>", methods=['POST'])
def set_user_data(session_id, data_name: str):
    """
    Sets user specific data provided by the browser - such as file uploads or webcam images

    :param session_id: The session's id
    :param data_name: The name of the data
    """
    session: Session = SessionHandler.shared_handler.get_session(session_id)
    SessionHandler.shared_handler.garbage_collect()
    if session is None:
        time.sleep(2.0)
        return Response(f"Error, invalid session", status=404)
    with session.lock:
        session.handle_used()
        if request.data is None:
            return Response(f"Error, invalid request", status=404)
        data = request.data
        if len(data) > MINIMUM_CAMERA_DATA_SIZE or not data_name.startswith("camera_"):  # can't be valid camera data if so small
            if request.data.startswith(b'data:'):
                b64_data = request.data.split(bytes(",", "ASCII"))[1]
                data = base64.b64decode(b64_data)
            session.set_user_data(data_name, data)
        session: SlideSession
        try:
            using_camera = session.get_needs_camera()
        except AttributeError:
            using_camera = False
    response = Response(f"OK", status=200)
    response.headers.set("usingCamera", "yes" if using_camera else "no")
    return make_uncacheable(response)


@slidestag_service.route("/dbg/sessionList", methods=['GET'])
def list_sessions():
    """
    Returns a list of all active sessions
    """
    session_data = []
    handler = SessionHandler.shared_handler
    SessionHandler.shared_handler.garbage_collect()
    sessions = []
    with handler.session_lock:
        for cur_session in handler.sessions.values():
            sessions.append(cur_session)
    for cur_session in sessions:
        cur_session: Session
        application: SlideApp = cur_session.app
        with cur_session.lock:
            cur_session_data = {
                "app": application.app_name,
                "idleTime": time.time() - cur_session.last_interaction,
                "id": cur_session.session_id,
                "guestId": cur_session.guest_id}
            if cur_session.guest_id is not None:
                cur_session_data['guestStream'] = f"{request.root_url}sessions/{cur_session.guest_id}/slideStream"
            session_data.append(cur_session_data)
    return make_uncacheable(jsonify(session_data))
