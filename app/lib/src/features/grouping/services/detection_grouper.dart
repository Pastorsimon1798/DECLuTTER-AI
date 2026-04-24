import '../../detect/domain/detection.dart';
import '../domain/detection_group.dart';

/// Utility for transforming raw detections into semantic groups.
class DetectionGrouper {
  const DetectionGrouper();

  /// Groups detections by their raw label and returns stable identifiers.
  List<DetectionGroup> groupDetections(List<Detection> detections) {
    if (detections.isEmpty) {
      return const [];
    }

    final Map<String, List<Detection>> grouped = {};
    for (final detection in detections) {
      final key = _normalizedLabel(detection.label);
      grouped.putIfAbsent(key, () => []).add(detection);
    }

    final entries = grouped.entries.toList()
      ..sort(
        (a, b) {
          final countCompare = b.value.length.compareTo(a.value.length);
          if (countCompare != 0) {
            return countCompare;
          }
          final labelA = a.value.first.displayLabel;
          final labelB = b.value.first.displayLabel;
          return labelA.compareTo(labelB);
        },
      );

    return [
      for (final entry in entries)
        DetectionGroup(
          id: _normalizedLabel(entry.value.first.label).replaceAll(RegExp(r'[^a-z0-9]'), '_'),
          rawLabel: entry.value.first.label,
          displayLabel: entry.value.first.displayLabel,
          detections: List.unmodifiable(entry.value),
        ),
    ];
  }

  String _normalizedLabel(String label) => label.trim().toLowerCase();
}
