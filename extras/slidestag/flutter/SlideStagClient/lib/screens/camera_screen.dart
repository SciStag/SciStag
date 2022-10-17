import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:developer';
import 'package:slidestag_flutter_client/widgets/slide_stag_session.dart';
import 'package:slidestag_flutter_client/widgets/slide_viewer.dart';
import 'package:slidestag_flutter_client/widgets/camera_not_available.dart';
import 'package:slidestag_flutter_client/main.dart';

/// The CameraScreen is a fullscreen widget which connects to a SlideStag
/// session, visualizing an image livestream provided by a server while
/// forwarding all inputs (and optionally the camera) to the server.
class CameraScreen extends StatefulWidget {
  const CameraScreen({Key? key}) : super(key: key);

  @override
  CameraScreenState createState() => CameraScreenState();
}

/// The CameraScreen's state
class CameraScreenState extends State<CameraScreen>
    with WidgetsBindingObserver {
  CameraController? controller;

  // Initial values
  /// Could the camera already be initialized successfully?
  bool _isCameraInitialized = false;

  /// Was access to the camera granted?
  bool _isCameraPermissionGranted = false;

  /// The server http url to which we have to connect to. Stored in the
  /// configuration file.
  String? _sessionUrl;

  /// A handle of the current session
  SlideStagSession? _session;

  /// The widget visualizing the image and catching the events
  SlideStagViewer? _slideStagViewer;

  final resolutionPresets = ResolutionPreset.values;

  ResolutionPreset currentResolutionPreset = ResolutionPreset.high;

  /// Check the camera's current status and update the UI once we got the
  /// permission to use it.
  getPermissionStatus() async {
    await Permission.camera.request();
    var status = await Permission.camera.status;

    if (status.isGranted) {
      log('Camera Permission granted');
      setState(() {
        _isCameraPermissionGranted = true;
      });
      onNewCameraSelected(cameras[1]);
    } else {
      log('Camera permission denied');
    }
  }

  /// Request a new session from the server. The server IP is fetched from
  /// the assets/config.json, see README
  void createSlideSession() async {
    final jsonString = await rootBundle.loadString(
      'assets/config.json',
    );
    final dynamic jsonMap = jsonDecode(jsonString);

    _sessionUrl = jsonMap['slideStag']['serverUrl'];
    _session = SlideStagSession(_sessionUrl!);
    _session?.setup();
  }

  /// When ever a new image could be retrieved, update it.
  void onNewImageAvailable(CameraImage image) {
    _session?.updateCameraImage(image);
  }

  /// Setup a new controller when ever a new camera was selected
  void onNewCameraSelected(CameraDescription cameraDescription) async {
    final previousCameraController = controller;

    final CameraController cameraController = CameraController(
      cameraDescription,
      currentResolutionPreset,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );

    await previousCameraController?.dispose();

    if (mounted) {
      setState(() {
        controller = cameraController;
      });
    }

    // Update UI if controller updated
    cameraController.addListener(() {
      if (mounted) setState(() {});
    });

    try {
      await cameraController.initialize();
      cameraController.startImageStream(onNewImageAvailable);
    } on CameraException catch (e) {
      log('Error initializing camera: $e');
    }
    if (mounted) {
      setState(() {
        _isCameraInitialized = controller!.value.isInitialized;
      });
    }
  }

  /// State initializer
  @override
  void initState() {
    // Hide the status bar in Android
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.manual, overlays: []);
    getPermissionStatus();
    createSlideSession();
    super.initState();
  }

  /// App state management
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final CameraController? cameraController = controller;
    if (cameraController == null || !cameraController.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      cameraController.dispose();
    } else if (state == AppLifecycleState.resumed) {
      onNewCameraSelected(cameraController.description);
    }
  }

  /// Disposal handling
  @override
  void dispose() {
    controller?.dispose();
    super.dispose();
  }

  /// Widget building
  @override
  Widget build(BuildContext context) {
    if (_isCameraPermissionGranted && _isCameraInitialized) {
      _slideStagViewer = SlideStagViewer(_session);
    }
    return SafeArea(
      child: Scaffold(
          backgroundColor: Colors.white,
          body: _isCameraPermissionGranted
              ? _isCameraInitialized
                  ? Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [_slideStagViewer ?? Container()])
                  : const Center(
                      child: Text(
                        'Connecting to server...',
                        style: TextStyle(color: Colors.white),
                      ),
                    )
              : CameraNotAvailableWidget(this)),
    );
  }
}
