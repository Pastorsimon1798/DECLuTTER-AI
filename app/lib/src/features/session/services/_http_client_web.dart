// Stub for web platform — HttpClient from dart:io is unavailable on web.
// ignore: avoid_classes_with_only_static_members
class ContentType {
  static const json = 'application/json';
}

// ignore: avoid_classes_with_only_static_members
class HttpHeaders {
  static const authorizationHeader = 'authorization';
}

class HttpClient {
  HttpClient();

  Duration? connectionTimeout;
  Duration idleTimeout = const Duration(seconds: 15);

  void close({bool force = false}) {}

  Future<HttpClientRequest> openUrl(String method, Uri url) async {
    throw UnsupportedError(
        'HttpClient is not available on web. Use the http package instead.');
  }
}

class HttpClientRequest {
  final HttpHeaders headers = HttpHeaders();
  void write(Object? object) {}
  Future<HttpClientResponse> close() async {
    throw UnsupportedError('HttpClient is not available on web.');
  }
}

class HttpClientResponse {
  int get statusCode => 0;
  Stream<List<int>> transform(dynamic converter) => const Stream.empty();
}
