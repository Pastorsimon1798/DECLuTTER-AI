import 'dart:ui';

import '../../detect/domain/detection.dart' show DetectionResult;
import '../services/detection_grouper.dart';
import 'detection_group.dart';

/// Summary of grouped detections produced from a raw [DetectionResult].
class GroupedDetectionResult {
  const GroupedDetectionResult({
    required this.groups,
    required this.totalDetections,
    required this.originalSize,
    required this.isMocked,
    this.inferenceTime,
  });

  const GroupedDetectionResult.empty()
      : groups = const [],
        totalDetections = 0,
        originalSize = Size.zero,
        isMocked = true,
        inferenceTime = null;

  /// Individual detection groups that should be presented to the user.
  final List<DetectionGroup> groups;

  /// Total number of detections that composed the groups.
  final int totalDetections;

  /// Original image size used to derive the detections.
  final Size originalSize;

  /// Whether the detections came from a mocked source (no on-device model).
  final bool isMocked;

  /// Time spent running inference if available.
  final Duration? inferenceTime;

  /// Total number of detected groups.
  int get groupCount => groups.length;

  /// Whether any user-facing groups are available.
  bool get hasGroups => groups.isNotEmpty;

  /// Returns the first group which should be preselected in the UI.
  DetectionGroup? get primaryGroup => groups.isEmpty ? null : groups.first;

  /// Finds a detection group by its identifier.
  DetectionGroup? groupForId(String? id) {
    if (id == null) {
      return null;
    }
    for (final group in groups) {
      if (group.id == id) {
        return group;
      }
    }
    return null;
  }

  /// Builds a [GroupedDetectionResult] from a raw [DetectionResult].
  factory GroupedDetectionResult.fromDetectionResult(
    DetectionResult result, {
    DetectionGrouper grouper = const DetectionGrouper(),
  }) {
    final groups = grouper.groupDetections(result.detections);
    return GroupedDetectionResult(
      groups: List.unmodifiable(groups),
      totalDetections: result.detections.length,
      originalSize: result.originalSize,
      isMocked: result.isMocked,
      inferenceTime: result.inferenceTime,
    );
  }
}
