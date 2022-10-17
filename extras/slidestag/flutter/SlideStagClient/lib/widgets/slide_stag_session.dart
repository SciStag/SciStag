import 'dart:async';
import 'dart:convert';
import 'dart:developer';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:image/image.dart' as img_lib;

typedef ImageUpdateCallback = void Function(Uint8List image);

/// Compresses and image and returns it's jpg byte data
compressImage(img_lib.Image imageHandle) {
  img_lib.JpegEncoder jpgEncoder = img_lib.JpegEncoder();
  jpgEncoder.setQuality(80);
  List<int> jpg = jpgEncoder.encodeImage(imageHandle);
  return jpg;
}

/// Represents a user touch input event
class SlideTouchEvent {
  /// The coordinate
  num x, y;

  /// The event, either "up", "down" or "move"
  String event;

  SlideTouchEvent(this.event, this.x, this.y);

  Map toJson() => {
        'type': event,
        'relative': true,
        'coord': [x, y]
      };
}

/// The SlideStag session holds all information about the remote execution of
/// a SlideStag application on a remote server.
class SlideStagSession {
  dynamic configuration;

  /// The configuration
  var valid = false;

  /// Defines if the communication could be established
  ImageUpdateCallback? onImageReceived;

  /// Update callback when a new image was received from the server
  VoidCallback? onSessionCreated;

  /// Update timer
  Timer? updateTimer;

  /// The URL (http) of the server we are communicating with
  String serverUrl;

  /// Execution depth counter to prevent async overlap
  var executing = 0;

  /// Defines if data is stream via MotionJPEG
  var useMjpegStreaming = false;

  /// Defines if we are waiting for a new image
  var awaitingNewImage = false;

  /// Defines if compression of the camera image is in progress
  var compressing = false;

  /// Defines if a camera is being used currently
  var usingCamera = false;

  /// Queue of events, e.g. user touch inputs, to be sent to the server
  List<SlideTouchEvent> eventList = [];

  /// The newest image
  img_lib.Image? newImage;
  /// Encoded image
  String? base64Image;

  /// The http client
  var dio = Dio();

  /// Constructor
  SlideStagSession(this.serverUrl,
      {this.onSessionCreated, this.onImageReceived});

  /// Adds a touch event to the queue. The queue is sent in regular intervals
  /// to the server.
  void addTouchEvent(String event, num x, num y) {
    eventList.add(SlideTouchEvent(event, x, y));
  }

  /// The main communication handler.
  /// Receives the newest image, sents input and optionally camera data.
  void updateData(Timer timer) async {
    if (useMjpegStreaming) return;

    if (executing > 1) {
      return;
    }

    awaitingNewImage = true;
    executing += 1;
    String singleImageUrl = configuration['singleImageUrl'];
    try {
      if (eventList.isNotEmpty) {
        var jsonData = jsonEncode(eventList);
        eventList.clear();
        final response = await dio.post(singleImageUrl,
            data: jsonData, options: Options(responseType: ResponseType.bytes));
        if (onImageReceived != null) {
          onImageReceived!(response.data);
        }
      } else {
        final response = await dio.post(singleImageUrl,
            data: base64Image,
            options: Options(responseType: ResponseType.bytes));
        // disable camera temporarily if idle
        if (response.headers.value('usingCamera') != null) {
          String usingCam = response.headers.value('usingCamera')!;
          usingCamera = usingCam == "yes";
        }
        if (base64Image != null) {
          base64Image = null;
        }
        if (onImageReceived != null) {
          onImageReceived!(response.data);
        }
      }
    } catch (e) {
      log("An error occurred while trying to receive the newest image from the SlideStag stream");
    } finally {}
    executing -= 1;

    if (newImage != null) {
      var image = newImage!;
      newImage = null;
      var result = compressImage(image);
      String base64String = base64Encode(result);
      String header = "data:image/jpg;base64,";
      base64Image = header + base64String;
    }
  }

  /// Try to compress the newest camera image.
  void updateCameraImage(CameraImage image) async {
    if (!usingCamera) {
      return;
    }
    if (!awaitingNewImage) {
      return;
    }
    if (compressing) {
      return;
    }
    compressing = true;
    var imageHandle = img_lib.Image.fromBytes(
      image.width,
      image.height,
      image.planes[0].bytes,
      format: img_lib.Format.bgra,
    );
    newImage = imageHandle;
    compressing = false;
  }

  /// Install main loop hook
  void setupMainLoopHook() {
    updateTimer = Timer.periodic(const Duration(milliseconds: 1), updateData);
  }

  /// Create a session
  Future<void> setup() async {
    try {
      log("Creating new SlideStag session");
      var response = await dio.get(
        serverUrl,
      );
      configuration = response.data;
      valid = true;
      if (onSessionCreated != null) onSessionCreated!();
      setupMainLoopHook();
      log("SlideStag session successfully created");
    } catch (e) {
      log("An error occurred while trying to create a SlideStag session");
    } finally {}
  }
}
