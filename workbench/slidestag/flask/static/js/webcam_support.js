let streamData = null;
let mainTrack = null;
let webcam_upload_url = "/sessions/" + session_id + "/postUserData/camera_00"
let webCamUploadFrequency = 100

// Put event listeners into place
window.addEventListener("DOMContentLoaded", function () {
    // Grab elements, create settings, etc.
    console.log("Initializing webcam...")
    var canvas = document.getElementById('canvas');
    var context = canvas.getContext('2d');
    var video = document.getElementById('video');
    var mediaConfig = {
        video: {
            facingMode: 'environment'
        }
    };
    var logError = function (e) {
        console.log('An error occurred:', e)
    };
    // Put video listeners into place
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia(mediaConfig).then(function (stream) {
            streamData = stream
            tracks = streamData.getVideoTracks();
            if (tracks.length === 0) {
                console.log("Error, no video tracks found");
                return;
            }
            mainTrack = tracks[0]
            let constraints = mainTrack.getConstraints()
            // let caps = mainTrack.getCapabilities()
            video.hidden = true;
            canvas.hidden = true;
            video.srcObject = stream;
            video.play();
        });
    } else if (navigator.getUserMedia) { // Standard
        navigator.getUserMedia(mediaConfig, function (stream) {
            video.src = stream;
            video.play();
        }, logError);
    } else if (navigator.webkitGetUserMedia) { // WebKit
        navigator.webkitGetUserMedia(mediaConfig, function (stream) {
            video.src = window.webkitURL.createObjectURL(stream);
            video.play();
        }, logError);
    } else if (navigator.mozGetUserMedia) { // Mozilla
        navigator.mozGetUserMedia(mediaConfig, function (stream) {
            video.src = window.URL.createObjectURL(stream);
            video.play();
        }, logError);
    }

    function update_image() {
        if(!window.usingCamera)  // skip camera data update if it's idle
        {
            setTimeout(update_image, webCamUploadFrequency);
            return;
        }
        if (canvas.width !== String(video.videoWidth) || canvas.height !== String(video.videoHeight)) {
            canvas.width = String(video.videoWidth);
            canvas.height = String(video.videoHeight);
            context = canvas.getContext('2d');
        }
        context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
        let jpeg_data = canvas.toDataURL("image/jpeg", 0.8);
        fetch(webcam_upload_url, {
            method: "POST",
            keepalive: true,
            headers: {'Content-Type': 'image/jpeg'},
            body: jpeg_data
        }).then(res => {
            setTimeout(update_image, webCamUploadFrequency);
        }).catch(function(error) { // just try again until server recovered
            setTimeout(update_image, webCamUploadFrequency);
        });
    }

    setTimeout(update_image, webCamUploadFrequency);
}, false);