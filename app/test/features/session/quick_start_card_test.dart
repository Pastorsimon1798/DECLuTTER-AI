import 'package:declutter_ai/src/features/session/presentation/widgets/quick_start_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('QuickStartCard renders title and tips', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: QuickStartCard(),
        ),
      ),
    );

    expect(find.text('Sorting this zone just got easier'), findsOneWidget);
    expect(
      find.textContaining('Decide: Keep, Sell or Donate'),
      findsOneWidget,
    );
    expect(find.text('Stay curious, not perfect.'), findsOneWidget);
    expect(find.text('Analysis stays on-device by default.'), findsOneWidget);
    expect(find.text('Need a breather? Pause or tap Maybe.'), findsOneWidget);
  });

  testWidgets('QuickStartCard renders tip chips with icons', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: QuickStartCard(),
        ),
      ),
    );

    expect(find.byType(Chip), findsNWidgets(3));
    expect(find.byIcon(Icons.lightbulb_outline), findsNWidgets(3));
  });
}
