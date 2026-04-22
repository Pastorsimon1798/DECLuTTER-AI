import 'dart:ui';

import 'package:declutter_ai/src/features/detect/domain/detection.dart';
import 'package:declutter_ai/src/features/grouping/domain/detection_group.dart';
import 'package:declutter_ai/src/features/grouping/domain/grouped_detection_result.dart';
import 'package:declutter_ai/src/features/session/domain/session_decision.dart';
import 'package:declutter_ai/src/features/session/presentation/session_timer_screen.dart';
import 'package:declutter_ai/src/features/session/services/cash_to_clear_api.dart';
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

GroupedDetectionResult buildGroupedResult(List<DetectionGroup> groups) {
  final totalDetections = groups.fold<int>(0, (sum, group) => sum + group.count);
  return GroupedDetectionResult(
    groups: groups,
    totalDetections: totalDetections,
    originalSize: const Size(400, 300),
    isMocked: false,
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
              groupedResult: buildGroupedResult(groups),
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
              groupedResult: const GroupedDetectionResult.empty(),
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
              groupedResult: buildGroupedResult(groups),
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

  group('SessionTimerScreen', () {
    testWidgets('surfaces grouped detections in the sprint UI', (tester) async {
      final groups = [
        buildGroup(id: 'group_1', label: 'books', count: 2),
        buildGroup(id: 'group_2', label: 'mug', count: 1),
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: SessionTimerScreen(
            groupedResult: buildGroupedResult(groups),
          ),
        ),
      );

      expect(find.text('Books · 0/2 sorted'), findsOneWidget);
      expect(find.text('Mug · 0/1 sorted'), findsOneWidget);
      expect(find.text('Books: 0/2 sorted'), findsOneWidget);
      expect(find.text('Mug: 0/1 sorted'), findsOneWidget);
    });

    testWidgets('logs decisions against the correct group metadata', (tester) async {
      final books = buildGroup(id: 'group_1', label: 'books', count: 2);
      final mug = buildGroup(id: 'group_2', label: 'mug', count: 1);

      await tester.pumpWidget(
        MaterialApp(
          home: SessionTimerScreen(
            groupedResult: buildGroupedResult([books, mug]),
          ),
        ),
      );

      await tester.tap(find.widgetWithText(FilledButton, 'Keep'));
      await tester.pumpAndSettle();

      // Save the decision without adding an optional note.
      await tester.tap(find.widgetWithText(FilledButton, 'Save decision'));
      await tester.pumpAndSettle();

      expect(find.text('Books · 1/2 sorted'), findsOneWidget);
      expect(find.text('Books: 1/2 sorted'), findsOneWidget);
      expect(find.textContaining('Progress: 1/2 items sorted'), findsOneWidget);
    });
  });

  group('CashToClearStatusCard', () {
    testWidgets('shows synced money on the table and group value chips', (tester) async {
      final groups = [
        buildGroup(id: 'group_1', label: 'books', count: 2),
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: Material(
            child: CashToClearStatusCard(
              isSyncing: false,
              message: 'Cash-to-Clear values synced.',
              moneyOnTableLowUsd: 12,
              moneyOnTableHighUsd: 30,
              groupedResult: buildGroupedResult(groups),
              publicListingUrlsByGroupId: const {
                'group_1': 'https://api.example.com/public/listings/pub_1',
              },
              creatingListingPageGroupIds: const {},
              onCreateListingPage: _noop,
              remoteItemsByGroupId: const {
                'group_1': CashToClearItemDto(
                  itemId: 'item_1',
                  label: 'books',
                  valuation: CashToClearValuationDto(
                    lowUsd: 12,
                    highUsd: 30,
                    confidence: 'medium',
                    source: 'mock-ebay-comps',
                  ),
                  listingDraft: CashToClearListingDraftDto(
                    title: 'Books - Unknown',
                    priceUsd: 21,
                    categoryHint: 'Books & Magazines',
                  ),
                ),
              },
            ),
          ),
        ),
      );

      expect(find.text('Money on the table'), findsOneWidget);
      expect(find.text(r'$12–30'), findsOneWidget);
      expect(find.textContaining('Books: \$12–30'), findsOneWidget);
      expect(find.text('Page created for Books'), findsOneWidget);
      expect(find.text('https://api.example.com/public/listings/pub_1'), findsOneWidget);
    });

    testWidgets('disables create page action while a group is already creating', (tester) async {
      final groups = [
        buildGroup(id: 'group_1', label: 'books', count: 2),
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: Material(
            child: CashToClearStatusCard(
              isSyncing: true,
              message: 'Creating standalone listing page...',
              moneyOnTableLowUsd: 12,
              moneyOnTableHighUsd: 30,
              groupedResult: buildGroupedResult(groups),
              publicListingUrlsByGroupId: const {},
              creatingListingPageGroupIds: const {'group_1'},
              onCreateListingPage: _noop,
              remoteItemsByGroupId: const {
                'group_1': CashToClearItemDto(
                  itemId: 'item_1',
                  label: 'books',
                  valuation: CashToClearValuationDto(
                    lowUsd: 12,
                    highUsd: 30,
                    confidence: 'medium',
                    source: 'mock-ebay-comps',
                  ),
                  listingDraft: CashToClearListingDraftDto(
                    title: 'Books - Unknown',
                    priceUsd: 21,
                    categoryHint: 'Books & Magazines',
                  ),
                ),
              },
            ),
          ),
        ),
      );

      final button = tester.widget<OutlinedButton>(
        find.widgetWithText(OutlinedButton, 'Creating page...'),
      );
      expect(button.onPressed, isNull);
    });
  });
}

void _noop(String _) {}

void _noopCategory(DecisionCategory _) {}
