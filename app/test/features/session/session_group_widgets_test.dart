import 'dart:ui';

import 'package:declutter_ai/src/features/detect/domain/detection.dart';
import 'package:declutter_ai/src/features/grouping/domain/detection_group.dart';
import 'package:declutter_ai/src/features/session/domain/session_decision.dart';
import 'package:declutter_ai/src/features/session/presentation/session_timer_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

DetectionGroup buildGroup({
  required String id,
  required String label,
  required int count,
}) {
  return DetectionGroup(
    id: id,
    rawLabel: label,
    displayLabel: label[0].toUpperCase() + label.substring(1),
    detections: List.generate(
      count,
      (index) => Detection(
        label: label,
        confidence: 0.9 - index * 0.1,
        boundingBox: Rect.fromLTWH(0.1 * index, 0, 0.2, 0.2),
      ),
    ),
  );
}

void main() {
  group('SessionDecisionComposer', () {
    testWidgets('shows group progress and enables actions when a group is selected', (tester) async {
      final groups = [
        buildGroup(id: 'group_1', label: 'books', count: 2),
        buildGroup(id: 'group_2', label: 'mug', count: 1),
      ];
      final decisions = [
        SessionDecision(
          groupId: 'group_1',
          groupLabel: groups.first.friendlyLabel,
          groupTotal: groups.first.count,
          category: DecisionCategory.keep,
          createdAt: DateTime(2024),
          note: 'Kept favorite novel',
        ),
      ];

      String? selectedGroup;
      DecisionCategory? selectedCategory;

      await tester.pumpWidget(
        MaterialApp(
          home: Material(
            child: SessionDecisionComposer(
              groups: groups,
              selectedGroupId: groups.first.id,
              onGroupSelected: (groupId) => selectedGroup = groupId,
              decisions: decisions,
              onCategorySelected: (category) => selectedCategory = category,
            ),
          ),
        ),
      );

      expect(find.text('Books · 1/2 sorted'), findsOneWidget);
      expect(find.text('Mug · 0/1 sorted'), findsOneWidget);

      await tester.tap(find.text('Mug · 0/1 sorted'));
      await tester.pumpAndSettle();
      expect(selectedGroup, 'group_2');

      await tester.tap(find.widgetWithText(FilledButton, 'Keep'));
      await tester.pumpAndSettle();
      expect(selectedCategory, DecisionCategory.keep);
    });

    testWidgets('disables action buttons when no groups detected', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Material(
            child: SessionDecisionComposer(
              groups: const [],
              selectedGroupId: null,
              onGroupSelected: _noop,
              decisions: const [],
              onCategorySelected: _noopCategory,
            ),
          ),
        ),
      );

      expect(find.text('No grouped detections yet. Capture a zone photo or retry analysis to unlock guided sorting.'), findsOneWidget);
      final keepButton = tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Keep'));
      expect(keepButton.onPressed, isNull);
    });
  });

  group('SessionDecisionHistory', () {
    testWidgets('summarizes group progress alongside logged decisions', (tester) async {
      final groups = [
        buildGroup(id: 'group_1', label: 'books', count: 2),
        buildGroup(id: 'group_2', label: 'mug', count: 1),
      ];
      final decisions = [
        SessionDecision(
          groupId: 'group_1',
          groupLabel: groups.first.friendlyLabel,
          groupTotal: groups.first.count,
          category: DecisionCategory.keep,
          createdAt: DateTime(2024, 1, 1, 10, 30),
          note: 'Shelved the novels',
        ),
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: Material(
            child: SessionDecisionHistory(
              decisions: decisions,
              groups: groups,
            ),
          ),
        ),
      );

      expect(find.text('Books: 1/2 sorted'), findsOneWidget);
      expect(find.text('Mug: 0/1 sorted'), findsOneWidget);
      expect(find.text('Group group_1 • Books (2 items)'), findsOneWidget);
      expect(find.text('Progress: 1/2 items sorted'), findsOneWidget);
      expect(find.text('Shelved the novels'), findsOneWidget);
    });
  });
}

void _noop(String _) {}

void _noopCategory(DecisionCategory _) {}
