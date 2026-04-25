import 'package:flutter/foundation.dart';

import '../../grouping/domain/grouped_detection_result.dart';
import '../../valuate/models/valuation.dart';
import '../domain/session_decision.dart';
import '../services/cash_to_clear_api.dart';

/// Base class for session states.
@immutable
sealed class SessionState {
  const SessionState();
}

/// Initial loading state while the session bootstraps.
@immutable
final class SessionLoading extends SessionState {
  const SessionLoading();
}

/// Terminal error state when bootstrapping fails irreversibly.
@immutable
final class SessionError extends SessionState {
  const SessionError(this.message);

  final String message;
}

/// Active session state holding all mutable data in an immutable snapshot.
@immutable
final class SessionActive extends SessionState {
  const SessionActive({
    required this.decisions,
    required this.selectedGroupId,
    required this.isSyncingCashToClear,
    required this.cashToClearSyncMessage,
    required this.moneyOnTableLowUsd,
    required this.moneyOnTableHighUsd,
    required this.remoteItemsByGroupId,
    required this.publicListingUrlsByGroupId,
    required this.creatingListingPageGroupIds,
    required this.isSprintCompleted,
    required this.groupedResult,
    required this.undoStack,
    required this.valuations,
    required this.valuationLoadingGroupIds,
  });

  final List<SessionDecision> decisions;
  final String? selectedGroupId;
  final bool isSyncingCashToClear;
  final String? cashToClearSyncMessage;
  final double? moneyOnTableLowUsd;
  final double? moneyOnTableHighUsd;
  final Map<String, CashToClearItemDto> remoteItemsByGroupId;
  final Map<String, String> publicListingUrlsByGroupId;
  final Set<String> creatingListingPageGroupIds;
  final bool isSprintCompleted;
  final GroupedDetectionResult groupedResult;
  final Map<String, List<SessionDecision>> undoStack;

  /// Per-group valuation estimates (null while loading or on error).
  final Map<String, Valuation?> valuations;

  /// Group IDs that are currently fetching a valuation.
  final Set<String> valuationLoadingGroupIds;

  int decisionCountForGroup(String groupId) =>
      decisions.where((d) => d.groupId == groupId).length;

  /// Returns the valuation for [groupId], if any.
  Valuation? valuationForGroup(String groupId) => valuations[groupId];

  /// Whether the valuation for [groupId] is currently being fetched.
  bool isValuationLoading(String groupId) =>
      valuationLoadingGroupIds.contains(groupId);

  /// Number of groups that have at least one decision.
  int get decidedCount {
    final decidedGroupIds = <String>{};
    for (final decision in decisions) {
      decidedGroupIds.add(decision.groupId);
    }
    return decidedGroupIds.length;
  }

  /// Whether every group has a decision.
  bool get allGroupsDecided =>
      groupedResult.hasGroups && decidedCount == groupedResult.groupCount;
}
