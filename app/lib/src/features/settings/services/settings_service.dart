import 'package:shared_preferences/shared_preferences.dart';

/// Runtime-configurable settings stored in SharedPreferences.
///
/// Replaces the compile-time-only dart-define approach so users can
/// connect to their self-hosted backend without rebuilding the app.
class SettingsService {
  SettingsService({SharedPreferences? prefs}) : _prefs = prefs;

  SharedPreferences? _prefs;

  Future<SharedPreferences> get _storage async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }

  static const _keyBaseUrl = 'declutter_api_base_url';
  static const _keyIdToken = 'declutter_id_token';
  static const _keyAppCheckToken = 'declutter_app_check_token';
  static const _keyUseServer = 'declutter_use_server';

  Future<String?> get baseUrl async {
    final prefs = await _storage;
    final value = prefs.getString(_keyBaseUrl);
    return value?.trim().isEmpty == true ? null : value?.trim();
  }

  Future<void> setBaseUrl(String? value) async {
    final prefs = await _storage;
    if (value == null || value.trim().isEmpty) {
      await prefs.remove(_keyBaseUrl);
    } else {
      await prefs.setString(_keyBaseUrl, value.trim());
    }
  }

  Future<String?> get idToken async {
    final prefs = await _storage;
    final value = prefs.getString(_keyIdToken);
    return value?.trim().isEmpty == true ? null : value?.trim();
  }

  Future<void> setIdToken(String? value) async {
    final prefs = await _storage;
    if (value == null || value.trim().isEmpty) {
      await prefs.remove(_keyIdToken);
    } else {
      await prefs.setString(_keyIdToken, value.trim());
    }
  }

  Future<String?> get appCheckToken async {
    final prefs = await _storage;
    final value = prefs.getString(_keyAppCheckToken);
    return value?.trim().isEmpty == true ? null : value?.trim();
  }

  Future<void> setAppCheckToken(String? value) async {
    final prefs = await _storage;
    if (value == null || value.trim().isEmpty) {
      await prefs.remove(_keyAppCheckToken);
    } else {
      await prefs.setString(_keyAppCheckToken, value.trim());
    }
  }

  Future<bool> get useServer async {
    final prefs = await _storage;
    return prefs.getBool(_keyUseServer) ?? false;
  }

  Future<void> setUseServer(bool value) async {
    final prefs = await _storage;
    await prefs.setBool(_keyUseServer, value);
  }

  Future<bool> get isConfigured async {
    final prefs = await _storage;
    final baseUrl = prefs.getString(_keyBaseUrl)?.trim() ?? '';
    final idToken = prefs.getString(_keyIdToken)?.trim() ?? '';
    final appCheckToken = prefs.getString(_keyAppCheckToken)?.trim() ?? '';
    final useServer = prefs.getBool(_keyUseServer) ?? false;
    return useServer && baseUrl.isNotEmpty && idToken.isNotEmpty && appCheckToken.isNotEmpty;
  }

  Future<void> clear() async {
    final prefs = await _storage;
    await prefs.remove(_keyBaseUrl);
    await prefs.remove(_keyIdToken);
    await prefs.remove(_keyAppCheckToken);
    await prefs.remove(_keyUseServer);
  }
}
