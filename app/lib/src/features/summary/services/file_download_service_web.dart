// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter

import 'dart:html';

/// Web implementation of [FileDownloadService] using blob URLs.
class FileDownloadService {
  static void download(String content, String filename, String mimeType) {
    final blob = Blob([content], mimeType);
    final url = Url.createObjectUrlFromBlob(blob);
    AnchorElement(href: url)
      ..download = filename
      ..click();
    Url.revokeObjectUrl(url);
  }
}
