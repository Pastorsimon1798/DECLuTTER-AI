import 'dart:math' as math;

import 'package:flutter/material.dart';

/// A single detection result produced by the on-device model.
///
/// Bounding boxes are normalized between 0.0 and 1.0 so they can be
/// scaled to any rendered size.
class Detection {
  const Detection({
    required this.label,
    required this.confidence,
    required this.boundingBox,
  });

  /// Raw label predicted by the detector.
  final String label;

  /// Confidence score between 0.0 and 1.0.
  final double confidence;

  /// Bounding box with normalized left, top, right, bottom coordinates.
  final Rect boundingBox;

  /// Returns a user-friendly label suitable for UI chips.
  String get displayLabel {
    if (label.isEmpty) {
      return 'Unknown';
    }
    final words =
        label.split(RegExp(r'[_\s]+')).where((word) => word.isNotEmpty);
    return words
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }

  /// Returns the bounding box scaled to a concrete [size].
  Rect scaledTo(Size size) {
    return Rect.fromLTRB(
      boundingBox.left * size.width,
      boundingBox.top * size.height,
      boundingBox.right * size.width,
      boundingBox.bottom * size.height,
    );
  }

  /// Clamps the bounding box so it always stays within bounds.
  Detection clamp() {
    final clamped = Rect.fromLTRB(
      boundingBox.left.clamp(0.0, 1.0),
      boundingBox.top.clamp(0.0, 1.0),
      boundingBox.right.clamp(0.0, 1.0),
      boundingBox.bottom.clamp(0.0, 1.0),
    );
    if (clamped == boundingBox) {
      return this;
    }
    return Detection(
      label: label,
      confidence: confidence,
      boundingBox: Rect.fromLTRB(
        math.min(clamped.left, clamped.right),
        math.min(clamped.top, clamped.bottom),
        math.max(clamped.left, clamped.right),
        math.max(clamped.top, clamped.bottom),
      ),
    );
  }
}

/// Aggregated detection result including metadata useful for UI overlays.
class DetectionResult {
  const DetectionResult({
    required this.detections,
    required this.originalSize,
    required this.isMocked,
    this.inferenceTime,
    this.mockReason,
  });

  /// Creates an empty result without detections.
  const DetectionResult.empty()
      : detections = const [],
        originalSize = Size.zero,
        isMocked = true,
        inferenceTime = null,
        mockReason = 'No detections available.';

  final List<Detection> detections;
  final Size originalSize;
  final bool isMocked;
  final Duration? inferenceTime;

  /// Human-readable explanation when [isMocked] is true.
  final String? mockReason;

  bool get isEmpty => detections.isEmpty;
}
