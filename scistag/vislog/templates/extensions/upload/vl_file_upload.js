let vlUploadUpdateProgress = {}; // Holds the upload state for all upload widgets
let vlUploadId = {}; // Holds IDs for each upload progress

// Based upon https://stackoverflow.com/questions/105034/how-do-i-create-a-guid-uuid
// from Jeff Ward
let guidLut = [];
for (let i = 0; i < 256; i++) {
    guidLut[i] = (i < 16 ? '0' : '') + (i).toString(16);
}

function vlCreateGuid() {
    let d0 = Math.random() * 0xffffffff | 0;
    let d1 = Math.random() * 0xffffffff | 0;
    let d2 = Math.random() * 0xffffffff | 0;
    let d3 = Math.random() * 0xffffffff | 0;
    return guidLut[d0 & 0xff] + guidLut[d0 >> 8 & 0xff] + guidLut[d0 >> 16 & 0xff] + guidLut[d0 >> 24 & 0xff] + '-' +
        guidLut[d1 & 0xff] + guidLut[d1 >> 8 & 0xff] + '-' + guidLut[d1 >> 16 & 0x0f | 0x40] + guidLut[d1 >> 24 & 0xff] + '-' +
        guidLut[d2 & 0x3f | 0x80] + guidLut[d2 >> 8 & 0xff] + '-' + guidLut[d2 >> 16 & 0xff] + guidLut[d2 >> 24 & 0xff] +
        guidLut[d3 & 0xff] + guidLut[d3 >> 8 & 0xff] + guidLut[d3 >> 16 & 0xff] + guidLut[d3 >> 24 & 0xff];
}

function vlFileDropAreaInitializeProgress(widget, numFiles) {
    let progressBar = document.getElementById(widget.id + '_PROGRESS')
    vlUploadUpdateProgress[widget.id] = []
    vlUploadId[widget.id] = vlCreateGuid()
    widget.dataset.uploadProgress = []
    progressBar.value = 0

    for (let i = numFiles; i > 0; i--) {
        vlUploadUpdateProgress[widget.id].push(0)
    }
}

function vlFileDropAreaUpdateProgress(widget, fileNumber, percent) {
    let progressBar = document.getElementById(widget.id + '_PROGRESS')
    vlUploadUpdateProgress[widget.id][fileNumber] = percent
    progressBar.value = vlUploadUpdateProgress[widget.id].reduce((tot, curr) => tot + curr, 0) / vlUploadUpdateProgress[widget.id].length
}

function vlFileDropAreaHandleFilesForUpload(widget, files) {
    let widget_gallery_name = widget.id + "_GALLERY"
    document.getElementById(widget_gallery_name).innerHTML = ""
    files = [...files]
    vlFileDropAreaInitializeProgress(widget, files.length)
    files.forEach(function (item, index) {
        vlDropAreaUploadFile(widget, item, index)
    })
    files.forEach(function (item, index) {
        vlDropAreaPreview(widget, item, index)
    })
}

function vlDropAreaPreview(widget, file) {
    let widget_gallery_name = widget.id + "_GALLERY";
    let file_extension = file.name.split(".").pop().toLowerCase();
    let image_extensions = ["bmp", "jpg", "jpeg", "gif", "png"];
    if (image_extensions.indexOf(file_extension) === -1) {
        return
    }
    let reader = new FileReader();
    reader.readAsDataURL(file)
    reader.onloadend = function () {
        let img = document.createElement('img')
        img.src = reader.result
        document.getElementById(widget_gallery_name).appendChild(img)
    }
}

function vlDropAreaUploadFile(widget, file, index) {
    let url = 'vl_upload_file'
    let xhr = new XMLHttpRequest()
    let formData = new FormData()
    xhr.open('POST', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')

    // Update progress (can be used to show progress indicator)
    xhr.upload.addEventListener("progress", function (e) {
        vlFileDropAreaUpdateProgress(widget, index, (e.loaded * 100.0 / e.total) || 100)
    })

    xhr.addEventListener('readystatechange', function (e) {
        if (xhr.readyState == 4 && xhr.status == 200) {
            vlFileDropAreaUpdateProgress(widget, index, 100) // <- Add this
        } else if (xhr.readyState == 4 && xhr.status != 200) {
            // Error. Inform the user
        }
    })

    formData.append("widget", widget.id)
    formData.append("uploadId", vlUploadId[widget.id])
    formData.append("fileIndex", index)
    formData.append("fileCount", vlUploadUpdateProgress[widget.id].length)
    formData.append('file', file)
    xhr.send(formData)
}

function vlSetupFileDropArea(widget) {
    function handleDrop(e) {
        let dt = e.dataTransfer
        let files = dt.files
        vlFileDropAreaHandleFilesForUpload(widget, files)
    }

    // ************************ Drag and drop ***************** //
    let dropArea = document.getElementById(widget.id + "_DROP_AREA")
        // Prevent default drag behaviors
    ;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false)
        document.body.addEventListener(eventName, preventDefaults, false)
    })
    // Highlight drop area when item is dragged over it
    ;['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false)
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false)
    })
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false)

    function preventDefaults(e) {
        e.preventDefault()
        e.stopPropagation()
    }

    function highlight(e) {
        dropArea.classList.add('highlight')
    }

    function unhighlight(e) {
        dropArea.classList.remove('active')
    }
}