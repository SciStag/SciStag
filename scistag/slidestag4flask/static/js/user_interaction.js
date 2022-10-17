let input_upload_url = "/sessions/" + session_id + "/postUserData/clientEvents"
let userDataUpdateFrequency = 100;
let eventSkips = 0; // amount of times no events were sent
let maxEventSkipsWhenStreaming = 10; // maximum amount of events to be allowed to skip when there is no other feedback channel
let inputUploadTimeout = 2.0
let lastMouseMovement = Date.now()
let mouseMoveFrequency = 1000 / 20 // up to 20fps
let trackMovement = false;
let mouseOrTouchDown = false
sliderFrame = document.getElementById("sliderFrame")
let sliderEvents = []
let eventLogging = true;

function getRelativePosition(evt) {
    let x, y;
    if (evt.type === 'touchstart' || evt.type === 'touchmove' || evt.type === 'touchend'
        || evt.type === 'touchcancel') {
        let orgEvt = (typeof evt.originalEvent === 'undefined') ? evt : evt.originalEvent;
        let touch = orgEvt.touches[0] || orgEvt.changedTouches[0];
        x = touch.pageX;
        y = touch.pageY;
    } else if (evt.type === 'mousedown' || evt.type === 'mouseup' || evt.type === 'mousemove' ||
        evt.type === 'mouseover' || evt.type === 'mouseout' || evt.type === 'mouseenter' ||
        evt.type === 'mouseleave') {
        x = evt.clientX;
        y = evt.clientY;
    }
    let rect = evt.currentTarget.getBoundingClientRect();
    return [x - rect.left, y - rect.top]
}

sliderFrame.addEventListener('mousedown', evt => {
    sliderEvents.push({"type": "mouseDown", "coord": getRelativePosition(evt)});
    mouseOrTouchDown = true;
    if (eventLogging) console.log("mouse down");
}, false);
sliderFrame.addEventListener('touchdown', evt => {
    sliderEvents.push({"type": "touchDown", "coord": getRelativePosition(evt)});
    mouseOrTouchDown = true;
}, false);
sliderFrame.addEventListener('mouseup', evt => {
    sliderEvents.push({"type": "mouseUp", "coord": getRelativePosition(evt)});
    if (eventLogging) console.log("mouse up");
    mouseOrTouchDown = false;
}, false);
sliderFrame.addEventListener('touchup', evt => {
    sliderEvents.push({"type": "touchUp", "coord": getRelativePosition(evt)});
    mouseOrTouchDown = false;
}, false);
sliderFrame.addEventListener('touchcancel', evt => {
    sliderEvents.push({"type": "touchCancel", "coord": getRelativePosition(evt)});
}, false);
sliderFrame.addEventListener('mousemove', evt => {
    if (mouseOrTouchDown) evt.preventDefault();
    let curTime = Date.now();
    if (curTime < lastMouseMovement + mouseMoveFrequency) return;
    if (!trackMovement) return;
    sliderEvents.push({"type": "mouseMove", "coord": getRelativePosition(evt)});
    lastMouseMovement = curTime;
}, false);
sliderFrame.addEventListener('touchmove', evt => {
    if (mouseOrTouchDown) evt.preventDefault();
    let curTime = Date.now();
    if (curTime < lastMouseMovement + mouseMoveFrequency) return;
    sliderEvents.push({"type": "touchMove", "coord": getRelativePosition(evt)});
    lastMouseMovement = curTime;
}, false);

function send_user_data() {
    if (sliderEvents.length === 0) {  // don't send data if there is none
        eventSkips += 1;
        if (eventSkips >= maxEventSkipsWhenStreaming && usingMjpeg) {
            eventSkips = 0;
            console.log("Synching with server");
        } else {
            setTimeout(send_user_data, userDataUpdateFrequency);
            return;
        }
    }
    let eventPackage = JSON.stringify(sliderEvents);
    sliderEvents = [];
    fetch(input_upload_url, {
        method: "POST",
        timeout: inputUploadTimeout,
        keepalive: true,
        headers: {'Content-Type': 'application/json'},
        body: eventPackage
    }).then(res => {
        window.usingCamera = res.headers.get("usingCamera") === "yes"; // update potentially modified cam state
        setTimeout(send_user_data, userDataUpdateFrequency);
    }).catch(function (error) { // just try again until server recovered
        setTimeout(send_user_data, userDataUpdateFrequency);
    });

}

setTimeout(send_user_data, userDataUpdateFrequency);