import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../domain/session_decision.dart';

/// Minimal stdlib-backed API client for the backend Cash-to-Clear session loop.
///
/// Configure at build/run time with:
///
/// ```bash
/// flutter run \
///   --dart-define=DECLUTTER_API_BASE_URL=https://api.example.com \
///   --dart-define=DECLUTTER_ID_TOKEN=<firebase-id-token> \
///   --dart-define=DECLUTTER_APP_CHECK_TOKEN=<app-check-token>
/// ```
///
/// When these values are absent, the Flutter UI stays in local-only mode.
class CashToClearApiClient {
  CashToClearApiClient({
    required String baseUrl,
    required String idToken,
    required String appCheckToken,
    HttpClient? httpClient,
  })  : baseUrl = _normalizeBaseUrl(baseUrl),
        _idToken = idToken,
        _appCheckToken = appCheckToken,
        _httpClient = httpClient ?? HttpClient() {
    _httpClient.connectionTimeout = const Duration(seconds: 10);
    _httpClient.idleTimeout = const Duration(seconds: 30);
  }

  factory CashToClearApiClient.fromEnvironment() {
    return CashToClearApiClient(
      baseUrl: const String.fromEnvironment('DECLUTTER_API_BASE_URL'),
      idToken: const String.fromEnvironment('DECLUTTER_ID_TOKEN'),
      appCheckToken: const String.fromEnvironment('DECLUTTER_APP_CHECK_TOKEN'),
    );
  }

  final String baseUrl;
  final String _idToken;
  final String _appCheckToken;
  final HttpClient _httpClient;

  bool get isConfigured =>
      baseUrl.isNotEmpty && _idToken.isNotEmpty && _appCheckToken.isNotEmpty;

  void dispose() {
    _httpClient.close();
  }

  Future<CashToClearSessionDto> createSession({String? imageStorageKey}) async {
    final response = await _requestJson(
      method: 'POST',
      path: '/sessions',
      body: imageStorageKey == null ? null : {'image_storage_key': imageStorageKey},
    );
    return CashToClearSessionDto.fromJson(response);
  }

  Future<CashToClearItemDto> addItem({
    required String sessionId,
    required String label,
    String condition = 'unknown',
  }) async {
    final response = await _requestJson(
      method: 'POST',
      path: '/sessions/$sessionId/items',
      body: {'label': label, 'condition': condition},
    );
    return CashToClearItemDto.fromJson(response);
  }

  Future<CashToClearDecisionDto> recordDecision({
    required String sessionId,
    required String itemId,
    required DecisionCategory category,
    String? note,
  }) async {
    final response = await _requestJson(
      method: 'POST',
      path: '/sessions/$sessionId/decisions',
      body: {
        'item_id': itemId,
        'decision': category.backendValue,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
    return CashToClearDecisionDto.fromJson(response);
  }

  Future<CashToClearPublicListingDto> createPublicListing({
    required String sessionId,
    required String itemId,
  }) async {
    final response = await _requestJson(
      method: 'POST',
      path: '/sessions/$sessionId/items/$itemId/public-listing',
    );
    return CashToClearPublicListingDto.fromJson(response, baseUrl: baseUrl);
  }

  Future<CashToClearSessionDto> getSession(String sessionId) async {
    final response = await _requestJson(method: 'GET', path: '/sessions/$sessionId');
    return CashToClearSessionDto.fromJson(response);
  }

  Future<Map<String, dynamic>> _requestJson({
    required String method,
    required String path,
    Map<String, dynamic>? body,
  }) async {
    if (!isConfigured) {
      throw const CashToClearApiException('Cash-to-Clear backend is not configured.');
    }

    final request = await _httpClient.openUrl(method, Uri.parse('$baseUrl$path'));
    request.headers.contentType = ContentType.json;
    request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $_idToken');
    request.headers.set('X-Firebase-AppCheck', _appCheckToken);

    if (body != null) {
      request.write(jsonEncode(body));
    }

    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();
    final decoded = responseBody.isEmpty ? <String, dynamic>{} : jsonDecode(responseBody);
    final json = decoded is Map<String, dynamic> ? decoded : <String, dynamic>{};

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = json['detail'];
      throw CashToClearApiException(
        detail is String ? detail : 'Backend request failed with status ${response.statusCode}.',
      );
    }

    return json;
  }

  static String _normalizeBaseUrl(String raw) {
    final trimmed = raw.trim();
    if (trimmed.endsWith('/')) {
      return trimmed.substring(0, trimmed.length - 1);
    }
    return trimmed;
  }
}

class CashToClearApiException implements Exception {
  const CashToClearApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class CashToClearSessionDto {
  const CashToClearSessionDto({
    required this.sessionId,
    required this.moneyOnTableLowUsd,
    required this.moneyOnTableHighUsd,
    required this.items,
  });

  factory CashToClearSessionDto.fromJson(Map<String, dynamic> json) {
    return CashToClearSessionDto(
      sessionId: json['session_id'] as String,
      moneyOnTableLowUsd: _readDouble(json['money_on_table_low_usd']),
      moneyOnTableHighUsd: _readDouble(json['money_on_table_high_usd']),
      items: (json['items'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(CashToClearItemDto.fromJson)
          .toList(growable: false),
    );
  }

  final String sessionId;
  final double moneyOnTableLowUsd;
  final double moneyOnTableHighUsd;
  final List<CashToClearItemDto> items;
}

class CashToClearItemDto {
  const CashToClearItemDto({
    required this.itemId,
    required this.label,
    required this.valuation,
    required this.listingDraft,
  });

  factory CashToClearItemDto.fromJson(Map<String, dynamic> json) {
    return CashToClearItemDto(
      itemId: json['item_id'] as String,
      label: json['label'] as String? ?? 'item',
      valuation: CashToClearValuationDto.fromJson(
        json['valuation'] as Map<String, dynamic>? ?? const {},
      ),
      listingDraft: CashToClearListingDraftDto.fromJson(
        json['listing_draft'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }

  final String itemId;
  final String label;
  final CashToClearValuationDto valuation;
  final CashToClearListingDraftDto listingDraft;
}

class CashToClearValuationDto {
  const CashToClearValuationDto({
    required this.lowUsd,
    required this.highUsd,
    required this.confidence,
    required this.source,
  });

  factory CashToClearValuationDto.fromJson(Map<String, dynamic> json) {
    return CashToClearValuationDto(
      lowUsd: _readDouble(json['estimated_low_usd']),
      highUsd: _readDouble(json['estimated_high_usd']),
      confidence: json['confidence'] as String? ?? 'unknown',
      source: json['source'] as String? ?? 'unknown',
    );
  }

  final double lowUsd;
  final double highUsd;
  final String confidence;
  final String source;
}

class CashToClearListingDraftDto {
  const CashToClearListingDraftDto({
    required this.title,
    required this.priceUsd,
    required this.categoryHint,
  });

  factory CashToClearListingDraftDto.fromJson(Map<String, dynamic> json) {
    return CashToClearListingDraftDto(
      title: json['title'] as String? ?? 'Listing draft',
      priceUsd: _readDouble(json['price_usd']),
      categoryHint: json['category_hint'] as String? ?? 'Everything Else',
    );
  }

  final String title;
  final double priceUsd;
  final String categoryHint;
}

class CashToClearDecisionDto {
  const CashToClearDecisionDto({required this.itemId, required this.decision});

  factory CashToClearDecisionDto.fromJson(Map<String, dynamic> json) {
    return CashToClearDecisionDto(
      itemId: json['item_id'] as String? ?? '',
      decision: json['decision'] as String? ?? '',
    );
  }

  final String itemId;
  final String decision;
}

class CashToClearPublicListingDto {
  const CashToClearPublicListingDto({
    required this.listingId,
    required this.publicUrl,
    required this.title,
  });

  factory CashToClearPublicListingDto.fromJson(
    Map<String, dynamic> json, {
    required String baseUrl,
  }) {
    final rawUrl = json['public_url'] as String? ?? '';
    return CashToClearPublicListingDto(
      listingId: json['listing_id'] as String? ?? '',
      publicUrl: rawUrl.startsWith('/') ? '$baseUrl$rawUrl' : rawUrl,
      title: json['title'] as String? ?? 'Public listing',
    );
  }

  final String listingId;
  final String publicUrl;
  final String title;
}

double _readDouble(Object? value) {
  if (value is num) {
    return value.toDouble();
  }
  return 0;
}

extension DecisionCategoryBackendValue on DecisionCategory {
  String get backendValue {
    switch (this) {
      case DecisionCategory.keep:
        return 'keep';
      case DecisionCategory.sell:
        return 'sell';
      case DecisionCategory.donate:
        return 'donate';
      case DecisionCategory.trash:
        return 'trash';
      case DecisionCategory.relocate:
        return 'relocate';
      case DecisionCategory.maybe:
        return 'maybe';
    }
  }
}
