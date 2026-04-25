import 'package:flutter/foundation.dart';
import 'package:share_plus/share_plus.dart';

import 'package:declutter_ai/src/features/session/domain/session_decision.dart';

import '../models/session_summary_data.dart';
import 'file_download_service.dart';

/// Generates and shares CSV exports of a completed sprint.
class CsvExportService {
  static String generateCsv(SessionSummaryData data) {
    final buffer = StringBuffer();
    buffer.writeln(
      'Group Name,Category,Decision,Note,Items Count,Low Value,Mid Value,High Value,Confidence',
    );

    for (final group in data.groupedResult.groups) {
      final decision = data.decisions[group.id];
      final valuation = data.valuations[group.id];
      final fields = [
        group.displayLabel,
        group.rawLabel,
        decision?.category.label ?? '',
        decision?.note ?? '',
        group.count.toString(),
        _formatDouble(valuation?.low),
        _formatDouble(valuation?.mid),
        _formatDouble(valuation?.high),
        valuation != null ? '${(valuation.confidence * 100).toStringAsFixed(0)}%' : '',
      ];
      buffer.writeln(fields.map(_escapeCsvField).join(','));
    }

    return buffer.toString();
  }

  static String _formatDouble(double? value) {
    if (value == null) return '';
    return value.toStringAsFixed(2);
  }

  static String _escapeCsvField(String value) {
    if (value.contains(',') || value.contains('"') || value.contains('\n')) {
      final escaped = value.replaceAll('"', '""');
      return '"$escaped"';
    }
    return value;
  }

  static Future<void> shareCsv(String csvContent, String filename) async {
    if (kIsWeb) {
      FileDownloadService.download(csvContent, filename, 'text/csv');
    } else {
      await Share.share(csvContent, subject: filename);
    }
  }
}
