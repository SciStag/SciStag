import 'package:flutter/material.dart';
import '../screens/camera_screen.dart';

/// The placeholder widget which is shown when the camera is not available
class CameraNotAvailableWidget extends StatelessWidget {
  final CameraScreenState camState;

  const CameraNotAvailableWidget(this.camState, {Key? key}) : super(key: key);

  /// On click update the status and try to get permission to the camera
  void getPermissionStatus() {
    camState.getPermissionStatus();
  }

  /// Widget builder
  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Row(),
        const Text(
          'Permission denied',
          style: TextStyle(
            color: Colors.white,
            fontSize: 24,
          ),
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: () {
            getPermissionStatus();
          },
          child: const Padding(
            padding: EdgeInsets.all(8.0),
            child: Text(
              'Give permission',
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
              ),
            ),
          ),
        ),
      ],
    );
  }
}