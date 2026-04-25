import '../../grouping/domain/grouped_detection_result.dart';
import '../../session/domain/session_decision.dart';
import '../../valuate/models/valuation.dart';

/// Immutable data holder for a completed sprint summary.
class SessionSummaryData {
  const SessionSummaryData({
    required this.groupedResult,
    required this.decisions,
    required this.valuations,
    required this.duration,
  });

  final GroupedDetectionResult groupedResult;
  final Map<String, SessionDecision> decisions;
  final Map<String, Valuation?> valuations;
  final Duration duration;

  int get totalItemsDecided => decisions.length;

  int countFor(DecisionCategory category) =>
      decisions.values.where((d) => d.category == category).length;

  int get keepCount => countFor(DecisionCategory.keep);
  int get donateCount => countFor(DecisionCategory.donate);
  int get trashCount => countFor(DecisionCategory.trash);
  int get relocateCount => countFor(DecisionCategory.relocate);
  int get maybeCount => countFor(DecisionCategory.maybe);

  double get totalResaleValue {
    var sum = 0.0;
    for (final entry in decisions.entries) {
      final category = entry.value.category;
      if (category == DecisionCategory.keep ||
          category == DecisionCategory.relocate) {
        final valuation = valuations[entry.key];
        if (valuation != null) {
          sum += valuation.mid;
        }
      }
    }
    return sum;
  }
}
