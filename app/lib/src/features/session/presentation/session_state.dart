import 'package:flutter/foundation.dart';

import '../../grouping/domain/grouped_detection_result.dart';
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

  int decisionCountForGroup(String groupId) =>
      decisions.where((d) => d.groupId == groupId).length;
}
