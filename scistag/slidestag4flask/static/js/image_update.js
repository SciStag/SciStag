screenImageUrl = "/sessions/" + session_id + "/screen"; //name of the image
screenImageTimeOut = 3000;
screenUpdateFrequency = 0;
usingCamera = false;
usingMjpeg = false;

function fetch_newest_image() {
    fetch(screenImageUrl, {
        method: "GET",
        keepalive: true,
        timeout: screenImageTimeOut,
    }).then(res => {
        window.usingCamera = res.headers.get("usingCamera") === "yes";
        setTimeout(fetch_newest_image, screenUpdateFrequency);
        res.arrayBuffer().then(data => {
            let binary = '';
            let bytes = new Uint8Array(data);
            let len = bytes.byteLength;
            for (var i = 0; i < len; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            fullData = 'data:image/jpg;base64,' + btoa(binary)
            document.getElementById('sliderFrame').src = fullData
        })
    }).catch(function (error) { // just try again until server recovered
        setTimeout(fetch_newest_image, screenUpdateFrequency);
    });
}

setTimeout(fetch_newest_image, screenUpdateFrequency);