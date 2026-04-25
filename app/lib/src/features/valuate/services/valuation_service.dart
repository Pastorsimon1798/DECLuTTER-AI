import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

import '../../grouping/domain/detection_group.dart';
import '../../session/services/_http_client.dart'
    if (dart.library.html) '../../session/services/_http_client_web.dart';
import '../models/valuation.dart';

/// Lightweight service that estimates resale value for a [DetectionGroup].
///
/// When the backend is configured it calls `POST /valuation`.  Otherwise it
/// falls back to a local lookup table so the UI never blocks.
class ValuationService {
  ValuationService({
    required String baseUrl,
    required String idToken,
    required String appCheckToken,
    HttpClient? httpClient,
  })  : _baseUrl = _normalizeBaseUrl(baseUrl),
        _idToken = idToken,
        _appCheckToken = appCheckToken,
        _httpClient = httpClient ?? HttpClient() {
    _httpClient.connectionTimeout = const Duration(seconds: 10);
    _httpClient.idleTimeout = const Duration(seconds: 30);
  }

  factory ValuationService.fromEnvironment() {
    return ValuationService(
      baseUrl: const String.fromEnvironment('DECLUTTER_API_BASE_URL'),
      idToken: const String.fromEnvironment('DECLUTTER_ID_TOKEN'),
      appCheckToken: const String.fromEnvironment('DECLUTTER_APP_CHECK_TOKEN'),
    );
  }

  final String _baseUrl;
  final String _idToken;
  final String _appCheckToken;
  final HttpClient _httpClient;

  bool get isConfigured =>
      !kIsWeb &&
      _baseUrl.isNotEmpty &&
      _idToken.isNotEmpty &&
      _appCheckToken.isNotEmpty;

  void dispose() {
    _httpClient.close();
  }

  /// Returns a [Valuation] for [group].
  ///
  /// If the backend is unavailable or the request fails, a locally-computed
  /// fallback estimate is returned so the UI can still show a range.
  Future<Valuation> estimateGroup(
    DetectionGroup group, {
    String? condition,
  }) async {
    final request = _ValuationRequest(
      category: group.displayLabel,
      count: group.count,
      condition: condition ?? 'unknown',
    );

    if (isConfigured) {
      try {
        final response = await _postValuation(request);
        return response;
      } on Exception catch (e) {
        debugPrint('Valuation backend failed: $e; using local fallback.');
      }
    }

    return _localFallback(request);
  }

  Future<Valuation> _postValuation(_ValuationRequest request) async {
    final req = await _httpClient.openUrl(
      'POST',
      Uri.parse('$_baseUrl/valuation'),
    );
    req.headers.contentType = ContentType.json;
    req.headers.set(HttpHeaders.authorizationHeader, 'Bearer $_idToken');
    req.headers.set('X-Firebase-AppCheck', _appCheckToken);
    req.write(jsonEncode(request.toJson()));

    final response = await req.close();
    final body = await response.transform(utf8.decoder).join();
    final decoded =
        body.isEmpty ? <String, dynamic>{} : jsonDecode(body);
    final json =
        decoded is Map<String, dynamic> ? decoded : <String, dynamic>{};

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = json['detail'];
      throw ValuationException(
        detail is String
            ? detail
            : 'Backend request failed with status ${response.statusCode}.',
      );
    }

    return Valuation.fromJson(json);
  }

  static Valuation _localFallback(_ValuationRequest request) {
    final ranges = <String, (double, double)>{
      'electronics': (10.0, 500.0),
      'books': (1.0, 15.0),
      'clothing': (2.0, 40.0),
      'furniture': (20.0, 300.0),
    };
    final multipliers = <String, double>{
      'new': 1.0,
      'good': 0.7,
      'fair': 0.4,
      'poor': 0.15,
    };

    final key = request.category.toLowerCase();
    final (lowBase, highBase) = ranges[key] ?? (1.0, 20.0);
    final multiplier = multipliers[request.condition.toLowerCase()] ?? 0.5;
    final low = lowBase * multiplier * request.count;
    final high = highBase * multiplier * request.count;
    final mid = (low + high) / 2;

    return Valuation(
      low: double.parse(low.toStringAsFixed(2)),
      mid: double.parse(mid.toStringAsFixed(2)),
      high: double.parse(high.toStringAsFixed(2)),
      confidence: 0.3,
    );
  }

  static String _normalizeBaseUrl(String raw) {
    final trimmed = raw.trim();
    if (trimmed.endsWith('/')) {
      return trimmed.substring(0, trimmed.length - 1);
    }
    return trimmed;
  }
}

class _ValuationRequest {
  const _ValuationRequest({
    required this.category,
    required this.condition,
    required this.count,
  });

  final String category;
  final String condition;
  final int count;

  Map<String, dynamic> toJson() => {
        'category': category,
        'condition': condition,
        'count': count,
      };
}

class ValuationException implements Exception {
  const ValuationException(this.message);

  final String message;

  @override
  String toString() => message;
}
