import 'package:declutter_ai/main.dart';
import 'package:declutter_ai/src/features/detect/domain/detection.dart';
import 'package:declutter_ai/src/features/grouping/domain/detection_group.dart';
import 'package:declutter_ai/src/features/grouping/domain/grouped_detection_result.dart';
import 'package:declutter_ai/src/features/session/presentation/session_timer_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('app boots to capture screen even when camera unavailable',
      (tester) async {
    await tester.pumpWidget(const DeclutterAIApp());

    // Allow the initial camera request future to resolve.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Capture clutter zone'), findsOneWidget);
    expect(find.text('Snap zone'), findsOneWidget);
    expect(find.byType(DeclutterHomeScreen), findsOneWidget);

    // Hidden trade tabs schedule short placeholder loads during app boot;
    // drain them so this boot smoke test does not leak pending fake timers.
    await tester.pump(const Duration(milliseconds: 600));
  });

  testWidgets('session timer logs decisions with notes', (tester) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    const group = DetectionGroup(
      id: 'group_1',
      rawLabel: 'keepsake box',
      displayLabel: 'Keepsake Box',
      detections: [
        Detection(
          label: 'keepsake box',
          confidence: 0.9,
          boundingBox: Rect.fromLTWH(0, 0, 0.4, 0.4),
        ),
      ],
    );

    await tester.pumpWidget(
      const MaterialApp(
        home: SessionTimerScreen(
          groupedResult: GroupedDetectionResult(
            groups: [group],
            totalDetections: 1,
            originalSize: Size(400, 300),
            isMocked: false,
          ),
        ),
      ),
    );

    await tester.scrollUntilVisible(
      find.widgetWithText(FilledButton, 'Keep'),
      120,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Keep'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byType(TextField),
      'Kept the keepsake box on the top shelf.',
    );

    expect(find.text('1/1 groups decided'), findsOneWidget);
  });
}
