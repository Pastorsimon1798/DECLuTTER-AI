/// Stub implementation of [FileDownloadService] for non-web platforms.
class FileDownloadService {
  static void download(String content, String filename, String mimeType) {
    throw UnsupportedError(
      'FileDownloadService is only supported on web.',
    );
  }
}
