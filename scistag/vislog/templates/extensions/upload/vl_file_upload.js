let vlUploadUpdateProgress = {}; // Holds the upload state for all upload widgets

function vlFileDropAreaInitializeProgress(widget, numFiles) {
    let progressBar = document.getElementById(widget.id + '_PROGRESS')
    vlUploadUpdateProgress[widget.id] = []
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
    let widget_gallery_name = widget.id + "_GALLERY"
    console.log(file.name)
    let reader = new FileReader()
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

    formData.append("fileIndex", index)
    formData.append("fileCount", len(vlUploadUpdateProgress[widget.id]))
    formData.append('file', file)
    xhr.send(formData)
}

function vlSetupFileDropArea(widget) {
    function handleDrop(e) {
        var dt = e.dataTransfer
        var files = dt.files
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
    });['dragleave', 'drop'].forEach(eventName => {
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