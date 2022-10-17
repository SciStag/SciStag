import 'dart:developer';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'screens/camera_screen.dart';
import 'dart:io';

/// List of all enumerated cameras
List<CameraDescription> cameras = [];

/// Allow access to self-created SSL certificates
class DevHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;
  }
}

/// Main entry point
Future<void> main() async {
  // Fetch the available cameras before initializing the app.
  HttpOverrides.global = DevHttpOverrides();
  try {
    WidgetsFlutterBinding.ensureInitialized();
    cameras = await availableCameras();
  } on CameraException catch (e) {
    log('An error occurred while initializing the camera', error: e);
  }
  runApp(const SlideStagClient());
}

/// The SlideStag client application main class
class SlideStagClient extends StatelessWidget {
  const SlideStagClient({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      debugShowCheckedModeBanner: false,
      home: const CameraScreen(),
    );
  }
}
