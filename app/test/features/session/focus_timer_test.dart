import 'package:declutter_ai/src/features/session/presentation/widgets/focus_timer.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('FocusTimer renders initial 10:00 state', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: FocusTimer(),
        ),
      ),
    );

    expect(find.text('10:00'), findsOneWidget);
    expect(find.text('Start'), findsOneWidget);
    expect(find.text('Reset'), findsOneWidget);
  });

  testWidgets('FocusTimer starts and shows pause button', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: FocusTimer(),
        ),
      ),
    );

    await tester.tap(find.text('Start'));
    await tester.pump();

    expect(find.text('Pause'), findsOneWidget);
    expect(find.text('Reset'), findsOneWidget);
  });

  testWidgets('FocusTimer pauses and shows start button', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: FocusTimer(),
        ),
      ),
    );

    await tester.tap(find.text('Start'));
    await tester.pump();
    expect(find.text('Pause'), findsOneWidget);

    await tester.tap(find.text('Pause'));
    await tester.pump();

    expect(find.text('Start'), findsOneWidget);
    expect(find.text('Reset'), findsOneWidget);
  });

  testWidgets('FocusTimer resets to initial duration', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: FocusTimer(),
        ),
      ),
    );

    await tester.tap(find.text('Start'));
    await tester.pump();
    expect(find.text('Pause'), findsOneWidget);

    await tester.tap(find.text('Pause'));
    await tester.pump();

    await tester.tap(find.text('Reset'));
    await tester.pump();

    expect(find.text('10:00'), findsOneWidget);
    expect(find.text('Start'), findsOneWidget);
  });

  testWidgets('FocusTimer timer callback fires while running',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: FocusTimer(),
        ),
      ),
    );

    await tester.tap(find.text('Start'));
    await tester.pump();

    // Pump one second to let the periodic timer callback execute.
    await tester.pump(const Duration(seconds: 1));

    // The timer should still be running (not completed after 1 second).
    expect(find.text('Pause'), findsOneWidget);
  });
}
