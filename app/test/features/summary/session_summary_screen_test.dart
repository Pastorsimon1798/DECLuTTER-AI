import 'package:declutter_ai/src/features/detect/domain/detection.dart';
import 'package:declutter_ai/src/features/grouping/domain/detection_group.dart';
import 'package:declutter_ai/src/features/grouping/domain/grouped_detection_result.dart';
import 'package:declutter_ai/src/features/session/domain/session_decision.dart';
import 'package:declutter_ai/src/features/summary/models/session_summary_data.dart';
import 'package:declutter_ai/src/features/valuate/models/valuation.dart';
import 'package:declutter_ai/src/features/summary/presentation/session_summary_screen.dart';
import 'package:declutter_ai/src/features/summary/services/csv_export_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('SessionSummaryScreen', () {
    final group1 = DetectionGroup(
      id: 'g1',
      rawLabel: 'books',
      displayLabel: 'Books',
      detections: List.generate(
        3,
        (i) => const Detection(
          label: 'books',
          confidence: 0.9,
          boundingBox: Rect.fromLTWH(0, 0, 0.1, 0.1),
        ),
      ),
    );

    const group2 = DetectionGroup(
      id: 'g2',
      rawLabel: 'mug',
      displayLabel: 'Mug',
      detections: [
        Detection(
          label: 'mug',
          confidence: 0.85,
          boundingBox: Rect.fromLTWH(0.2, 0.2, 0.1, 0.1),
        ),
      ],
    );

    final groupedResult = GroupedDetectionResult(
      groups: [group1, group2],
      totalDetections: 4,
      originalSize: const Size(400, 300),
      isMocked: false,
    );

    final decisions = <String, SessionDecision>{
      'g1': SessionDecision(
        groupId: 'g1',
        groupLabel: 'Books',
        groupTotal: 3,
        category: DecisionCategory.keep,
        createdAt: DateTime(2026, 4, 24),
        note: 'Keep on shelf',
      ),
      'g2': SessionDecision(
        groupId: 'g2',
        groupLabel: 'Mug',
        groupTotal: 1,
        category: DecisionCategory.donate,
        createdAt: DateTime(2026, 4, 24),
      ),
    };

    final valuations = <String, Valuation?>{
      'g1': const Valuation(low: 5, mid: 10, high: 15, confidence: 'high'),
      'g2': null,
    };

    testWidgets('renders with data and shows correct counts', (tester) async {
      tester.view.physicalSize = const Size(800, 2000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        MaterialApp(
          home: SessionSummaryScreen(
            groupedResult: groupedResult,
            decisions: decisions,
            valuations: valuations,
            sessionDuration: const Duration(minutes: 5, seconds: 30),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Sprint Complete! 🎉'), findsOneWidget);
      expect(find.text('You sorted 2 items in 05:30.'), findsOneWidget);
      expect(find.text('Keep'), findsNWidgets(2));
      expect(find.text('Donate'), findsNWidgets(2));
      expect(find.text('1'), findsNWidgets(2));
      expect(find.text('Trash'), findsOneWidget);
      expect(find.text('0'), findsNWidgets(3));
      expect(find.text('\$10.00'), findsOneWidget);
      expect(find.text('Keep on shelf'), findsOneWidget);
      expect(find.text('Export CSV'), findsOneWidget);
      expect(find.text('Start New Sprint'), findsOneWidget);
    });

    testWidgets('start new sprint callback is invoked', (tester) async {
      tester.view.physicalSize = const Size(800, 2000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      var called = false;
      await tester.pumpWidget(
        MaterialApp(
          home: SessionSummaryScreen(
            groupedResult: groupedResult,
            decisions: decisions,
            valuations: valuations,
            sessionDuration: Duration.zero,
            onStartNewSprint: () => called = true,
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Start New Sprint'));
      await tester.pumpAndSettle();
      expect(called, isTrue);
    });
  });

  group('CsvExportService', () {
    test('generates correct CSV content with escaping', () {
      const group = DetectionGroup(
        id: 'g1',
        rawLabel: 'books',
        displayLabel: 'Books',
        detections: [
          Detection(
            label: 'books',
            confidence: 0.9,
            boundingBox: Rect.fromLTWH(0, 0, 0.1, 0.1),
          ),
        ],
      );

      final data = SessionSummaryData(
        groupedResult: const GroupedDetectionResult(
          groups: [group],
          totalDetections: 1,
          originalSize: Size(400, 300),
          isMocked: false,
        ),
        decisions: {
          'g1': SessionDecision(
            groupId: 'g1',
            groupLabel: 'Books',
            groupTotal: 1,
            category: DecisionCategory.keep,
            createdAt: DateTime(2026),
            note: 'Note with "quotes", and commas',
          ),
        },
        valuations: {
          'g1': const Valuation(low: 1, mid: 2, high: 3, confidence: 'high'),
        },
        duration: Duration.zero,
      );

      final csv = CsvExportService.generateCsv(data);
      final lines = csv.split('\n');
      expect(
        lines[0],
        'Group Name,Category,Decision,Note,Items Count,Low Value,Mid Value,High Value,Confidence',
      );
      expect(
        lines[1],
        'Books,books,Keep,"Note with ""quotes"", and commas",1,1.00,2.00,3.00,high',
      );
    });

    test('handles empty decisions and valuations gracefully', () {
      const group = DetectionGroup(
        id: 'g1',
        rawLabel: 'mug',
        displayLabel: 'Mug',
        detections: [
          Detection(
            label: 'mug',
            confidence: 0.8,
            boundingBox: Rect.fromLTWH(0, 0, 0.1, 0.1),
          ),
        ],
      );

      const data = SessionSummaryData(
        groupedResult: GroupedDetectionResult(
          groups: [group],
          totalDetections: 1,
          originalSize: Size(400, 300),
          isMocked: false,
        ),
        decisions: {},
        valuations: {},
        duration: Duration.zero,
      );

      final csv = CsvExportService.generateCsv(data);
      final lines = csv.split('\n');
      expect(lines[1], 'Mug,mug,,,1,,,,');
    });
  });
}
