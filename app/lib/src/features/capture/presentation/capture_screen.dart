import 'dart:async';
import 'dart:io' show File;

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../detect/domain/detection.dart';
import '../../detect/presentation/widgets/detection_debug_painter.dart';
import '../../detect/services/detector_service.dart';
import '../../grouping/domain/grouped_detection_result.dart';
import '../../grouping/services/detection_grouper.dart';
import '../../session/presentation/session_timer_screen.dart';

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen>
    with WidgetsBindingObserver {
  CameraController? _controller;
  XFile? _lastCapture;
  Uint8List? _lastCaptureBytes;
  String? _lastCapturePersistentPath;
  bool _isRequesting = true;
  bool _permissionDenied = false;
  bool _cameraUnavailable = false;
  String? _errorMessage;
  final DetectorService _detectorService = DetectorService();
  DetectionResult? _detectionResult;
  GroupedDetectionResult _groupedResult = const GroupedDetectionResult.empty();
  bool _isAnalyzingCapture = false;
  String? _analysisError;
  final DetectionGrouper _detectionGrouper = const DetectionGrouper();
  Future<void>? _cameraInitFuture;
  bool _disposed = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_detectorService.initialize());
    _cameraInitFuture = _initCamera();
  }

  @override
  void dispose() {
    _disposed = true;
    WidgetsBinding.instance.removeObserver(this);
    _cameraInitFuture?.ignore();
    _controller?.dispose();
    _detectorService.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      controller.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initCamera(reopen: true);
    }
  }

  Future<void> _initCamera({bool reopen = false}) async {
    if (_disposed || !mounted) return;
    setState(() {
      _isRequesting = true;
      if (!reopen) {
        _cameraUnavailable = false;
        _permissionDenied = false;
        _errorMessage = null;
        _lastCapture = null;
        _lastCaptureBytes = null;
        _detectionResult = null;
        _groupedResult = const GroupedDetectionResult.empty();
        _analysisError = null;
        _isAnalyzingCapture = false;
      }
    });

    try {
      final permissionStatus = await Permission.camera.request();
      if (!mounted) return;
      if (!permissionStatus.isGranted) {
        setState(() {
          _permissionDenied = true;
          _isRequesting = false;
        });
        return;
      }
    } on PlatformException catch (error) {
      if (!mounted) return;
      setState(() {
        _cameraUnavailable = true;
        _errorMessage = error.message ??
            'Camera permission is unavailable in this environment.';
        _isRequesting = false;
      });
      return;
    }

    try {
      final cameras = await availableCameras();
      if (!mounted) return;
      if (cameras.isEmpty) {
        setState(() {
          _cameraUnavailable = true;
          _errorMessage =
              'No camera detected. Try another device or simulator with camera support.';
          _isRequesting = false;
        });
        return;
      }

      final CameraDescription camera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      final controller = CameraController(
        camera,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await controller.initialize();
      if (_disposed || !mounted) {
        await controller.dispose();
        return;
      }

      _controller?.dispose();
      if (_disposed) {
        await controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _isRequesting = false;
      });
    } on CameraException catch (error) {
      if (!mounted) return;
      setState(() {
        _cameraUnavailable = true;
        _errorMessage = error.description ?? 'Unable to start camera preview.';
        _isRequesting = false;
      });
    } on PlatformException catch (error) {
      if (!mounted) return;
      setState(() {
        _cameraUnavailable = true;
        _errorMessage =
            error.message ?? 'Camera is not available in this environment.';
        _isRequesting = false;
      });
    }
  }

  Future<void> _capturePhoto() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return;
    }

    try {
      final capture = await controller.takePicture();
      if (!mounted) return;
      final bytes = await capture.readAsBytes();
      if (!mounted) return;

      String? persistentPath;
      if (!kIsWeb) {
        try {
          final original = File(capture.path);
          final destDir = original.parent;
          final timestamp = DateTime.now().millisecondsSinceEpoch;
          persistentPath = '${destDir.path}/declutter_capture_$timestamp.jpg';
          await original.copy(persistentPath);
        } catch (e) {
          debugPrint('Failed to persist capture: $e');
          persistentPath = capture.path;
        }
      }

      setState(() {
        _lastCapture = capture;
        _lastCaptureBytes = bytes;
        _lastCapturePersistentPath = persistentPath;
      });
      if (!kIsWeb) {
        unawaited(_analyzeCaptureWithFeedback(capture));
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Photo saved. Review below before sorting.')),
      );
    } on CameraException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(
                'Could not capture photo: ${error.description ?? error.code}')),
      );
    }
  }

  void _openSessionTimer() {
    final path = _lastCapturePersistentPath ?? _lastCapture?.path;
    if (path == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Capture a photo first to start sorting.')),
      );
      return;
    }

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SessionTimerScreen(
          capturedImagePath: path,
          capturedAt: DateTime.now(),
          groupedResult: _groupedResult,
        ),
      ),
    );
  }

  Future<void> _analyzeCaptureWithFeedback(XFile capture) async {
    try {
      await _analyzeCapture(capture);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Analysis failed: $error'),
          duration: const Duration(seconds: 4),
          action: SnackBarAction(
            label: 'DISMISS',
            onPressed: () {
              ScaffoldMessenger.of(context).hideCurrentSnackBar();
            },
          ),
        ),
      );
    }
  }

  Future<void> _analyzeCapture(XFile capture) async {
    setState(() {
      _isAnalyzingCapture = true;
      _analysisError = null;
      _detectionResult = null;
      _groupedResult = const GroupedDetectionResult.empty();
    });

    try {
      final result = await _detectorService.detectOnImage(capture.path);
      if (!mounted) return;
      setState(() {
        _detectionResult = result;
        _groupedResult = GroupedDetectionResult.fromDetectionResult(
          result,
          grouper: _detectionGrouper,
        );
        _isAnalyzingCapture = false;
      });
      if (result.isMocked && result.mockReason != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Demo mode: ${result.mockReason}'),
            duration: const Duration(seconds: 4),
            action: SnackBarAction(
              label: 'DISMISS',
              onPressed: () {
                ScaffoldMessenger.of(context).hideCurrentSnackBar();
              },
            ),
          ),
        );
      }
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _analysisError = error.toString();
        _isAnalyzingCapture = false;
      });
    }
  }

  Widget _buildPreview() {
    if (_isRequesting) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_permissionDenied) {
      return _MessageCard(
        icon: Icons.lock_outline,
        title: 'Camera permission needed',
        message:
            'Allow camera access so the app can analyze your clutter zone. Tap retry after enabling permissions.',
        actionLabel: 'Retry',
        onTap: _initCamera,
      );
    }

    if (_cameraUnavailable ||
        _controller == null ||
        !_controller!.value.isInitialized) {
      return _MessageCard(
        icon: Icons.videocam_off_outlined,
        title: 'Camera preview unavailable',
        message: _errorMessage ??
            'We could not start the camera. If you are on a simulator or running tests, use a real device to try again.',
        actionLabel: 'Retry',
        onTap: _initCamera,
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: AspectRatio(
        aspectRatio: _controller!.value.aspectRatio,
        child: CameraPreview(_controller!),
      ),
    );
  }

  Widget _buildReviewCard() {
    final capture = _lastCapture;
    if (capture == null) {
      return const _MessageCard(
        icon: Icons.photo_camera_back_outlined,
        title: 'No photo yet',
        message:
            'Line up one small zone and tap the shutter. You will see the preview here when it is ready.',
      );
    }

    return Card(
      elevation: 0,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (!kIsWeb)
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(12)),
              child: AspectRatio(
                aspectRatio: _previewAspectRatio(),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    Image.memory(
                      _lastCaptureBytes!,
                      fit: BoxFit.cover,
                    ),
                    if (_detectionResult != null && !_detectionResult!.isEmpty)
                      CustomPaint(
                        size: Size.infinite,
                        painter: DetectionDebugPainter(_detectionResult!),
                      ),
                    if (_isAnalyzingCapture)
                      Container(
                        color: Colors.black54,
                        child: const Center(
                          child: CircularProgressIndicator(),
                        ),
                      ),
                    if (_analysisError != null)
                      Container(
                        color: Colors.black54,
                        alignment: Alignment.center,
                        padding: const EdgeInsets.all(16),
                        child: const Text(
                          'Analysis failed. Try another snap with steadier lighting.',
                          style: TextStyle(color: Colors.white),
                          textAlign: TextAlign.center,
                        ),
                      ),
                  ],
                ),
              ),
            )
          else
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                  'Preview unsupported on this platform, but the capture path is saved.'),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Ready to sort this zone?',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  'When you continue, DECLuTTER AI will run on-device detection and group suggestions.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 12),
                _buildAnalysisStatus(),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _openSessionTimer,
                  icon: const Icon(Icons.play_arrow_rounded),
                  label: const Text('Start 10-min timer & sort'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  double _previewAspectRatio() {
    final result = _detectionResult;
    if (result != null &&
        result.originalSize.width > 0 &&
        result.originalSize.height > 0) {
      return result.originalSize.width / result.originalSize.height;
    }
    final controller = _controller;
    if (controller != null && controller.value.isInitialized) {
      return controller.value.aspectRatio;
    }
    return 4 / 3;
  }

  Widget _buildAnalysisStatus() {
    if (kIsWeb) {
      return const Text(
          'Detection preview is coming soon for web builds. Continue to practice the flow.');
    }

    if (_isAnalyzingCapture) {
      return const Row(
        children: [
          SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Text(
                'Mapping groups... keep breathing. We will highlight likely clusters next.'),
          ),
        ],
      );
    }

    if (_analysisError != null) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.orange),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'We could not analyze that photo. Try snapping again with steadier lighting.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      );
    }

    final result = _detectionResult;
    if (result == null) {
      return const Text(
          'Tap "Snap zone" to analyze a photo and see debug boxes for detected groups.');
    }

    if (result.isEmpty) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'No groups spotted. Try a closer photo or brighter light so the model can find items.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      );
    }

    final detectionCount = result.detections.length;
    final groupCount = _groupedResult.groupCount;
    final statusText = result.isMocked
        ? 'Showing sample detections (add assets/model/detector.tflite to use the real model).'
        : 'Detected $detectionCount items across $groupCount groups in your zone.';
    final inferenceText = result.inferenceTime != null
        ? 'Inference: ${result.inferenceTime!.inMilliseconds} ms'
        : 'Inference running locally.';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(result.isMocked ? Icons.bug_report_outlined : Icons.insights,
                color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                statusText,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          inferenceText,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 8),
        if (_groupedResult.hasGroups)
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _groupedResult.groups
                .map(
                  (group) => Chip(
                    avatar: const Icon(Icons.group_work_outlined),
                    label: Text(
                      '${group.friendlyLabel} · ${(group.averageConfidence * 100).toStringAsFixed(0)}%',
                    ),
                  ),
                )
                .toList(),
          )
        else
          const Text(
            'No clear group clusters yet. Snap another angle or get a bit closer for better grouping.',
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Capture clutter zone'),
        actions: [
          Semantics(
            button: true,
            label: 'Capture tips',
            child: IconButton(
              onPressed: () {
                showModalBottomSheet(
                  context: context,
                  showDragHandle: true,
                  builder: (_) {
                    return const Padding(
                      padding: EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Quick capture checklist',
                            style: TextStyle(
                                fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          SizedBox(height: 12),
                          Text('• Pick a single shelf, drawer, or desk zone.'),
                          SizedBox(height: 8),
                          Text('• Clear big distractions (coffee cups, cords).'),
                          SizedBox(height: 8),
                          Text(
                              '• Breathe. One photo now; decisions happen next.'),
                        ],
                      ),
                    );
                  },
                );
              },
              icon: const Icon(Icons.help_outline),
              tooltip: 'Capture tips',
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Expanded(
                child: _buildPreview(),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  FloatingActionButton.extended(
                    onPressed: !_isRequesting &&
                            !_permissionDenied &&
                            !_cameraUnavailable
                        ? _capturePhoto
                        : null,
                    icon: const Icon(Icons.camera_alt_outlined),
                    label: const Text('Snap zone'),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: _initCamera,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Reset view'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildReviewCard(),
            ],
          ),
        ),
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Icon(icon, size: 48, color: theme.colorScheme.primary),
            const SizedBox(height: 16),
            Text(
              title,
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: theme.textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            if (actionLabel != null) ...[
              const SizedBox(height: 16),
              FilledButton(
                onPressed: onTap,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
