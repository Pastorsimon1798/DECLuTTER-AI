import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:declutter_ai/src/features/settings/services/settings_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  group('SettingsService', () {
    test('isConfigured returns false when empty', () async {
      final service = SettingsService();
      expect(await service.isConfigured, isFalse);
    });

    test('stores and retrieves base URL', () async {
      final service = SettingsService();
      await service.setBaseUrl('https://example.com');
      expect(await service.baseUrl, 'https://example.com');
    });

    test('isConfigured returns true when all fields set and useServer true', () async {
      final service = SettingsService();
      await service.setBaseUrl('https://example.com');
      await service.setIdToken('token');
      await service.setAppCheckToken('check');
      await service.setUseServer(true);
      expect(await service.isConfigured, isTrue);
    });

    test('clear removes all values', () async {
      final service = SettingsService();
      await service.setBaseUrl('https://example.com');
      await service.setUseServer(true);
      await service.clear();
      expect(await service.baseUrl, isNull);
      expect(await service.useServer, isFalse);
    });
  });
}
