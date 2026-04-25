import 'package:declutter_ai/src/features/capture/presentation/capture_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const permissionChannel =
      MethodChannel('flutter.baseflow.com/permissions/methods');

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(permissionChannel, null);
  });

  testWidgets('CaptureScreen shows permission denied state', (tester) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(permissionChannel, (call) async {
      if (call.method == 'requestPermissions') {
        return <int, int>{1: 0}; // camera=1, denied=0
      }
      return null;
    });

    await tester.pumpWidget(
      const MaterialApp(
        home: CaptureScreen(),
      ),
    );

    // Allow the async permission request to resolve.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('Camera permission needed'), findsOneWidget);
    expect(
      find.textContaining(
        'Allow camera access so the app can analyze your clutter zone.',
      ),
      findsOneWidget,
    );
    expect(find.text('Retry'), findsOneWidget);
  });

  testWidgets('CaptureScreen shows camera unavailable on PlatformException',
      (tester) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(permissionChannel, (call) async {
      throw PlatformException(
        code: 'PERMISSION_NOT_SUPPORTED',
        message: 'Camera permission is unavailable in this environment.',
      );
    });

    await tester.pumpWidget(
      const MaterialApp(
        home: CaptureScreen(),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('Camera preview unavailable'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
  });
}
