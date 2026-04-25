import 'package:flutter/material.dart';

import 'package:flutter_test/flutter_test.dart';

import 'package:declutter_ai/src/features/detect/domain/detection.dart';
import 'package:declutter_ai/src/features/grouping/services/detection_grouper.dart';

void main() {
  group('DetectionGrouper', () {
    const grouper = DetectionGrouper();

    test('returns empty list when there are no detections', () {
      expect(grouper.groupDetections(const []), isEmpty);
    });

    test('groups detections by normalized label', () {
      final groups = grouper.groupDetections(
        [
          const Detection(
            label: 'books',
            confidence: 0.9,
            boundingBox: Rect.fromLTWH(0, 0, 0.5, 0.5),
          ),
          const Detection(
            label: 'Books ',
            confidence: 0.8,
            boundingBox: Rect.fromLTWH(0.1, 0.1, 0.4, 0.4),
          ),
          const Detection(
            label: 'mug',
            confidence: 0.95,
            boundingBox: Rect.fromLTWH(0.2, 0.2, 0.3, 0.3),
          ),
        ],
      );

      expect(groups, hasLength(2));
      expect(groups.first.id, 'books');
      expect(groups.first.displayLabel, 'Books');
      expect(groups.first.count, 2);
      expect(groups.first.friendlyLabel, 'Books (2 items)');
      expect(groups.last.displayLabel, 'Mug');
      expect(groups.last.count, 1);
    });
  });
}
