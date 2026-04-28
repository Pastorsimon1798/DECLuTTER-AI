import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:declutter_ai/src/features/detect/services/backend_analysis_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  group('BackendAnalysisService', () {
    test('returns null when not configured', () async {
      final service = BackendAnalysisService();
      final result = await service.analyzeImage('path');
      expect(result, isNull);
    });

    test('returns detections on successful backend response', () async {
      SharedPreferences.setMockInitialValues({
        'declutter_api_base_url': 'https://api.example.com',
        'declutter_id_token': 'token',
        'declutter_app_check_token': 'appcheck',
        'declutter_use_server': true,
      });

      final mockClient = MockClient((request) async {
        if (request.url.path == '/analysis/intake') {
          return http.Response(jsonEncode({'storage_key': 'abc123'}), 200);
        }
        if (request.url.path == '/analysis/run') {
          return http.Response(
            jsonEncode({
              'items': [
                {'label': 'book', 'confidence': 0.92},
                {'label': 'phone', 'confidence': 0.85},
              ]
            }),
            200,
          );
        }
        return http.Response('Not Found', 404);
      });

      final service = BackendAnalysisService(httpClient: mockClient);
      final result = await service.analyzeImage(
        'path',
        imageBytes: Uint8List.fromList([1, 2, 3]),
      );

      expect(result, isNotNull);
      expect(result!.detections.length, 2);
      expect(result.detections.first.label, 'book');
      expect(result.isMocked, isFalse);
    });

    test('returns null on backend error', () async {
      SharedPreferences.setMockInitialValues({
        'declutter_api_base_url': 'https://api.example.com',
        'declutter_id_token': 'token',
        'declutter_app_check_token': 'appcheck',
        'declutter_use_server': true,
      });

      final mockClient = MockClient((request) async {
        return http.Response('Server Error', 500);
      });

      final service = BackendAnalysisService(httpClient: mockClient);
      final result = await service.analyzeImage(
        'path',
        imageBytes: Uint8List(0),
      );

      expect(result, isNull);
    });
  });
}
