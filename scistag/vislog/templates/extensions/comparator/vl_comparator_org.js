//! Initializes an LComparator widget. Pass in the upper level view which is going to
//! be resized
function vlSetupComparator(overlay)
{
    let slider, touch_down = 0, width, height;
    width = overlay.offsetWidth;
    height = overlay.offsetHeight;
    overlay.style.width = (width / 2) + "px";
    slider = document.createElement("div");
    slider.setAttribute("class", "vl-comp-slider");
    overlay.parentElement.insertBefore(slider, overlay);
    slider.style.top = (height / 2) - (slider.offsetHeight / 2) + "px";
    slider.style.left = (width / 2) - (slider.offsetWidth / 2) + "px";
    slider.addEventListener("mousedown", handleTouch);
    window.addEventListener("mouseup", handleRelease);
    slider.addEventListener("touchstart", handleTouch);
    window.addEventListener("touchend", handleRelease);

    function handleTouch(e) {
        e.preventDefault();
        touch_down = 1;
        window.addEventListener("mousemove", handleMove);
        window.addEventListener("touchmove", handleMove);
    }

    function handleRelease() {
        touch_down = 0;
    }

    function handleMove(e) {
        let pos;
        if (touch_down === 0) {
            return false;
        }
        pos = getCursorPos(e)
        if (pos < 0) pos = 0;
        if (pos > width) pos = width;
        slide(pos);
    }

    function getCursorPos(e) {
        let area, x = 0;
        e = (e.changedTouches) ? e.changedTouches[0] : e;
        area = overlay.getBoundingClientRect();
        x = e.pageX - area.left;
        x = x - window.pageXOffset;
        return x;
    }

    function slide(x) {
        overlay.style.width = x + "px";
        slider.style.left = overlay.offsetWidth - (slider.offsetWidth / 2) + "px";
    }
}