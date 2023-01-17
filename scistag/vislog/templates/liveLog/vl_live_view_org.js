/** Handles the value change of an input component */
function vl_handle_value_changed(element, value) {
    vl_values[element] = String(value); // store value for next sync
}

function setInnerHTML(elm, html) {
    elm.innerHTML = html;

    Array.from(elm.querySelectorAll("script"))
        .forEach(oldScriptEl => {
            const newScriptEl = document.createElement("script");

            Array.from(oldScriptEl.attributes).forEach(attr => {
                newScriptEl.setAttribute(attr.name, attr.value)
            });

            const scriptText = document.createTextNode(oldScriptEl.innerHTML);
            newScriptEl.appendChild(scriptText);

            oldScriptEl.parentNode.replaceChild(newScriptEl, oldScriptEl);
        });
}

/** Handles if the server sent a content change request */
function vl_handle_set_content(headers, data) {
    let targetElement = headers.get("targetElement")
    let element = document.getElementById(targetElement);
    if (element === null) {
        console.log("Unknown element " + targetElement);
        return;
    }
    // if(vl_log_updates){ console.log("Updating " + targetElement); }
    setInnerHTML(element, data)
}

/** Is called on intervals and asks the server for modifications. The sleep time
 till the next update is automatically by the server */
function fetch_changes() {
    let data_body = {"values": vl_values}
    vl_values = {}; // clear changes

    fetch(vl_fetch_url, {
        method: "POST",
        body: JSON.stringify(data_body),
        keepalive: true,
        timeout: pageUpdateTimeout,
    }).then(res => {
        setTimeout(fetch_changes, pageUpdateFrequency);
        if (vl_lost_connection) {
            vl_lost_connection = false;
            console.log("Server connection restored");
        }
        if (res.status !== 200) {
            return;
        }
        pageUpdateFrequency = parseInt(res.headers.get("vlRefreshTime"))
        res.text().then(data => {
            let action = res.headers.get("action")
            if (action === "setContent") {
                vl_handle_set_content(res.headers, data)
            }
        })
    }).catch(function (error) { // just try again until server recovered
        if (!vl_lost_connection) {
            vl_lost_connection = true;
            console.log("Lost connection to the server")
        }
        setTimeout(fetch_changes, 2000);
    });
}