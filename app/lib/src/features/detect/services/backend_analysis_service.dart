import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../settings/services/settings_service.dart';
import '../domain/detection.dart';

/// Uploads images to the backend for AI-powered analysis when on-device
/// inference is unavailable (e.g. web builds without a model).
class BackendAnalysisService {
  BackendAnalysisService({
    SettingsService? settings,
    http.Client? httpClient,
  })  : _settings = settings ?? SettingsService(),
        _httpClient = httpClient ?? http.Client();

  final SettingsService _settings;
  final http.Client _httpClient;

  /// Checks whether the backend is configured by reading settings.
  Future<bool> checkConfigured() async {
    return await _settings.isConfigured;
  }

  /// Analyzes an image by uploading it to the backend.
  ///
  /// Returns [DetectionResult] with real AI-detected items, or `null` if the
  /// backend is not configured or the request fails.
  Future<DetectionResult?> analyzeImage(
    String imagePath, {
    Uint8List? imageBytes,
    Size imageSize = const Size(1280, 720),
  }) async {
    if (!await _settings.isConfigured) {
      return null;
    }

    final baseUrl = await _settings.baseUrl;
    final idToken = await _settings.idToken;
    final appCheckToken = await _settings.appCheckToken;

    if (baseUrl == null || baseUrl.isEmpty) {
      return null;
    }

    final normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;

    try {
      // 1. Upload the image
      final bytes = imageBytes ?? await _readImageBytes(imagePath);
      if (bytes == null || bytes.isEmpty) {
        debugPrint('BackendAnalysisService: no image bytes available');
        return null;
      }

      final uploadRequest = http.MultipartRequest(
        'POST',
        Uri.parse('$normalizedBaseUrl/analysis/intake'),
      );
      uploadRequest.files.add(
        http.MultipartFile.fromBytes(
          'image',
          bytes,
          filename: 'capture.jpg',
        ),
      );
      if (idToken != null && idToken.isNotEmpty) {
        uploadRequest.headers['Authorization'] = 'Bearer $idToken';
      }
      if (appCheckToken != null && appCheckToken.isNotEmpty) {
        uploadRequest.headers['X-Firebase-AppCheck'] = appCheckToken;
      }

      final uploadResponse = await _httpClient.send(uploadRequest);
      final uploadBody = await uploadResponse.stream.bytesToString();

      if (uploadResponse.statusCode < 200 || uploadResponse.statusCode >= 300) {
        debugPrint('BackendAnalysisService: upload failed ${uploadResponse.statusCode}: $uploadBody');
        return null;
      }

      final uploadJson = jsonDecode(uploadBody) as Map<String, dynamic>;
      final storageKey = uploadJson['storage_key'] as String?;
      if (storageKey == null || storageKey.isEmpty) {
        debugPrint('BackendAnalysisService: no storage_key in upload response');
        return null;
      }

      // 2. Run analysis
      final analysisRequest = await _httpClient.post(
        Uri.parse('$normalizedBaseUrl/analysis/run'),
        headers: {
          'Content-Type': 'application/json',
          if (idToken != null && idToken.isNotEmpty)
            'Authorization': 'Bearer $idToken',
          if (appCheckToken != null && appCheckToken.isNotEmpty)
            'X-Firebase-AppCheck': appCheckToken,
        },
        body: jsonEncode({
          'image_storage_key': storageKey,
          'session_id': 'web_${DateTime.now().millisecondsSinceEpoch}',
        }),
      );

      if (analysisRequest.statusCode < 200 || analysisRequest.statusCode >= 300) {
        debugPrint('BackendAnalysisService: analysis failed ${analysisRequest.statusCode}: ${analysisRequest.body}');
        return null;
      }

      final analysisJson = jsonDecode(analysisRequest.body) as Map<String, dynamic>;
      final items = analysisJson['items'] as List<dynamic>? ?? const [];

      final detections = <Detection>[];
      for (var i = 0; i < items.length; i++) {
        final item = items[i] as Map<String, dynamic>;
        final label = item['label'] as String?;
        final confidence = (item['confidence'] as num?)?.toDouble() ?? 0.5;
        if (label == null || label.isEmpty) continue;

        // Distribute detections evenly across the image for visual feedback
        final cols = (items.length / 2).ceil();
        final row = i ~/ cols;
        final col = i % cols;
        final cellW = 1.0 / cols;
        final cellH = 1.0 / ((items.length / cols).ceil());
        final left = col * cellW + cellW * 0.1;
        final top = row * cellH + cellH * 0.1;
        final right = left + cellW * 0.8;
        final bottom = top + cellH * 0.8;

        detections.add(Detection(
          label: label,
          confidence: confidence.clamp(0.0, 1.0),
          boundingBox: Rect.fromLTRB(left, top, right, bottom),
        ));
      }

      return DetectionResult(
        detections: detections,
        originalSize: imageSize,
        isMocked: false,
        inferenceTime: const Duration(milliseconds: 800),
      );
    } catch (e) {
      debugPrint('BackendAnalysisService: analysis error: $e');
      return null;
    }
  }

  Future<Uint8List?> _readImageBytes(String imagePath) async {
    if (kIsWeb) {
      // On web, imagePath is a blob URL — we should have gotten bytes from the caller
      return null;
    }
    try {
      final file = File(imagePath);
      if (await file.exists()) {
        return file.readAsBytes();
      }
    } catch (e) {
      debugPrint('BackendAnalysisService: failed to read file: $e');
    }
    return null;
  }

  void dispose() {
    _httpClient.close();
  }
}
