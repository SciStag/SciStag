import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';
import 'package:slidestag_flutter_client/widgets/slide_stag_session.dart';

/// Visualizes the current slide and collect it's touch events
class SlideStagViewer extends StatefulWidget {
  final SlideStagSession? session;

  const SlideStagViewer(this.session, {Key? key}) : super(key: key);

  @override
  State<SlideStagViewer> createState() => _SlideStagViewerState();
}

/// The SlideStagViewer's state
class _SlideStagViewerState extends State<SlideStagViewer> {
  /// The SlideStag session we are using
  SlideStagSession? session;
  /// The current image, still encoded
  Uint8List? currentImage;

  _SlideStagViewerState();

  @override
  void initState() {
    super.initState();
    session = widget.session;
    session?.onSessionCreated = sessionCreated;
    session?.onImageReceived = imageUpdate;
  }

  /// Called when the session was successfully initialized
  void sessionCreated() {
    setState(() {});
  }

  /// Called when a new image is available
  void imageUpdate(image) {
    setState(() {
      currentImage = image;
    });
  }

  /// Collect tap down events and send then to server server
  void _handleTapDown(TapDownDetails details) {
    final RenderObject? referenceBox = context.findRenderObject();
    setState(() {
      if (referenceBox != null && context.size != null && session != null) {
        var relX = details.localPosition.dx / context.size!.width;
        var relY = details.localPosition.dy / context.size!.height;
        session!.addTouchEvent("tapDown", relX, relY);
      }
    });
  }

  /// Collect tap up evens and send them to the server
  void _handleTapUp(TapUpDetails details) {
    final RenderObject? referenceBox = context.findRenderObject();
    setState(() {
      if (referenceBox != null && context.size != null && session != null) {
        var relX = details.localPosition.dx / context.size!.width;
        var relY = details.localPosition.dy / context.size!.height;
        session!.addTouchEvent("tapUp", relX, relY);
      }
    });
  }

  /// Build function
  @override
  Widget build(BuildContext context) {
    return session?.configuration != null && session?.useMjpegStreaming == true
        ? Mjpeg(isLive: true, stream: session!.configuration['streamUrl'])
        : currentImage != null
            ? GestureDetector(
                child: Image.memory(currentImage!, gaplessPlayback: true),
                onTapDown: _handleTapDown,
                onTapUp: _handleTapUp)
            : Container(color: Colors.white);
  }
}
