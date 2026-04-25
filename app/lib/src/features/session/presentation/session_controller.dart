import 'package:flutter/foundation.dart';

import '../../grouping/domain/detection_group.dart';
import '../../grouping/domain/grouped_detection_result.dart';
import '../../valuate/models/valuation.dart';
import '../../valuate/services/valuation_service.dart';
import '../domain/session_decision.dart';
import '../services/cash_to_clear_api.dart';
import 'session_state.dart';

/// Business-logic controller for a declutter sprint session.
///
/// Holds decision state, remote sync state, and drives the Cash-to-Clear
/// backend integration. Notifies listeners on every meaningful state change.
class SessionController extends ChangeNotifier {
  SessionController({
    required GroupedDetectionResult groupedResult,
    CashToClearApiClient? cashToClearApi,
    ValuationService? valuationService,
  })  : _groupedResult = groupedResult,
        _cashToClearApi =
            cashToClearApi ?? CashToClearApiClient.fromEnvironment(),
        _valuationService =
            valuationService ?? ValuationService.fromEnvironment() {
    _ownsCashToClearApi = cashToClearApi == null;
    _ownsValuationService = valuationService == null;
    if (_groupedResult.hasGroups) {
      _selectedGroupId = _groupedResult.primaryGroup?.id;
    }
    _bootstrapCashToClearSession();
    _bootstrapValuations();
  }

  final GroupedDetectionResult _groupedResult;
  final CashToClearApiClient _cashToClearApi;
  final ValuationService _valuationService;
  bool _ownsCashToClearApi = false;
  bool _ownsValuationService = false;
  bool _disposed = false;

  final List<SessionDecision> _decisions = [];
  final Map<String, List<SessionDecision>> _undoStack = {};
  final Map<String, CashToClearItemDto> _remoteItemsByGroupId = {};
  final Map<String, String> _publicListingUrlsByGroupId = {};
  final Set<String> _creatingListingPageGroupIds = {};
  final List<_PendingRemoteDecision> _pendingRemoteDecisions = [];
  final Map<String, Valuation?> _valuations = {};
  final Set<String> _valuationLoadingGroupIds = {};
  String? _selectedGroupId;
  String? _remoteSessionId;
  double? _moneyOnTableLowUsd;
  double? _moneyOnTableHighUsd;
  bool _isSyncingCashToClear = false;
  String? _cashToClearSyncMessage;
  bool _isSprintCompleted = false;

  /// Current immutable snapshot of the session state.
  SessionState get state => SessionActive(
        decisions: List.unmodifiable(_decisions),
        selectedGroupId: _selectedGroupId,
        isSyncingCashToClear: _isSyncingCashToClear,
        cashToClearSyncMessage: _cashToClearSyncMessage,
        moneyOnTableLowUsd: _moneyOnTableLowUsd,
        moneyOnTableHighUsd: _moneyOnTableHighUsd,
        remoteItemsByGroupId: Map.unmodifiable(_remoteItemsByGroupId),
        publicListingUrlsByGroupId:
            Map.unmodifiable(_publicListingUrlsByGroupId),
        creatingListingPageGroupIds:
            Set.unmodifiable(_creatingListingPageGroupIds),
        isSprintCompleted: _isSprintCompleted,
        groupedResult: _groupedResult,
        undoStack: Map.unmodifiable({
          for (final entry in _undoStack.entries)
            entry.key: List.unmodifiable(entry.value),
        }),
        valuations: Map.unmodifiable(_valuations),
        valuationLoadingGroupIds:
            Set.unmodifiable(_valuationLoadingGroupIds),
      );

  String? get selectedGroupId => _selectedGroupId;

  GroupedDetectionResult get groupedResult => _groupedResult;

  void selectGroup(String groupId) {
    _selectedGroupId = groupId;
    _notify();
  }

  /// Validates whether a decision can be logged for the currently selected
  /// group. Returns an error message or `null` when valid.
  String? validateDecision(DecisionCategory category) {
    final selectedGroup = _groupedResult.groupForId(_selectedGroupId);
    if (selectedGroup == null) {
      return 'Select a highlighted group before logging a decision.';
    }
    final alreadyDecided = _decisions.any(
      (d) => d.groupId == selectedGroup.id && d.category == category,
    );
    if (alreadyDecided) {
      return 'You already decided "${category.label}" for ${selectedGroup.friendlyLabel}.';
    }
    return null;
  }

  /// Returns the current decision for a group, if any.
  SessionDecision? decisionForGroup(String groupId) {
    for (final decision in _decisions) {
      if (decision.groupId == groupId) {
        return decision;
      }
    }
    return null;
  }

  /// Records a new decision for [groupId], replacing any existing decision
  /// for that group. The previous decision is pushed onto the undo stack.
  Future<void> addDecision(
    String groupId,
    DecisionCategory category, {
    String? note,
  }) async {
    final group = _groupedResult.groupForId(groupId);
    if (group == null) return;

    final current = decisionForGroup(groupId);
    if (current != null) {
      _undoStack.putIfAbsent(groupId, () => []).add(current);
    }

    _decisions.removeWhere((d) => d.groupId == groupId);
    _decisions.insert(
      0,
      SessionDecision(
        groupId: group.id,
        groupLabel: group.friendlyLabel,
        groupTotal: group.count,
        category: category,
        createdAt: DateTime.now(),
        note: note,
      ),
    );
    _notify();

    await _recordRemoteDecision(
      group: group,
      category: category,
      note: note,
    );
  }

  /// Restores the previous decision for [groupId] from the undo stack.
  /// If the stack is empty, the current decision is simply removed.
  void undoDecision(String groupId) {
    final stack = _undoStack[groupId];
    if (stack != null && stack.isNotEmpty) {
      final previous = stack.removeLast();
      _decisions.removeWhere((d) => d.groupId == groupId);
      _decisions.insert(0, previous);
    } else {
      _decisions.removeWhere((d) => d.groupId == groupId);
    }
    _notify();
  }

  /// Creates a public listing page for the given group on the backend.
  Future<void> createPublicListingPage(String groupId) async {
    final sessionId = _remoteSessionId;
    final remoteItem = _remoteItemsByGroupId[groupId];
    if (!_cashToClearApi.isConfigured ||
        sessionId == null ||
        remoteItem == null) {
      _cashToClearSyncMessage =
          'Sync Cash-to-Clear values before creating a page.';
      _notify();
      return;
    }

    _isSyncingCashToClear = true;
    _creatingListingPageGroupIds.add(groupId);
    _cashToClearSyncMessage = 'Creating standalone listing page...';
    _notify();

    try {
      final listing = await _cashToClearApi.createPublicListing(
        sessionId: sessionId,
        itemId: remoteItem.itemId,
      );
      _publicListingUrlsByGroupId[groupId] = listing.publicUrl;
      _creatingListingPageGroupIds.remove(groupId);
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage = 'Standalone listing page created.';
      _notify();
    } catch (error) {
      debugPrint('Cash-to-Clear public listing creation failed: $error');
      _creatingListingPageGroupIds.remove(groupId);
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage =
          'Could not create listing page. Please try again.';
      _notify();
    }
  }

  /// Marks the sprint as completed (e.g. when the timer runs out).
  void completeSprint() {
    _isSprintCompleted = true;
    _notify();
  }

  /// Resets the sprint to its initial state.
  void resetSprint() {
    _isSprintCompleted = false;
    _decisions.clear();
    _undoStack.clear();
    _selectedGroupId =
        _groupedResult.hasGroups ? _groupedResult.primaryGroup?.id : null;
    _moneyOnTableLowUsd = null;
    _moneyOnTableHighUsd = null;
    _valuations.clear();
    _valuationLoadingGroupIds.clear();
    _notify();
    _bootstrapValuations();
  }

  /// Manually retry valuation for a single group (e.g. after a network error).
  Future<void> retryValuation(String groupId) async {
    final group = _groupedResult.groupForId(groupId);
    if (group == null) return;
    await _fetchValuation(group);
  }

  Future<void> _bootstrapValuations() async {
    if (!_groupedResult.hasGroups) return;

    await Future.wait(
      _groupedResult.groups.map((group) => _fetchValuation(group)),
    );
  }

  Future<void> _fetchValuation(DetectionGroup group) async {
    _valuationLoadingGroupIds.add(group.id);
    _notify();

    try {
      final valuation = await _valuationService.estimateGroup(
        group,
        condition: 'unknown',
      );
      _valuations[group.id] = valuation;
    } on Exception catch (e) {
      debugPrint('Valuation fetch failed for ${group.id}: $e');
      _valuations[group.id] = null;
    } finally {
      _valuationLoadingGroupIds.remove(group.id);
      _notify();
    }
  }

  Future<void> _bootstrapCashToClearSession() async {
    if (!_cashToClearApi.isConfigured || !_groupedResult.hasGroups) {
      _cashToClearSyncMessage = _cashToClearApi.isConfigured
          ? 'Cash-to-Clear backend is ready. Capture detections to sync values.'
          : 'Local mode: add DECLUTTER_API_BASE_URL, DECLUTTER_ID_TOKEN, and DECLUTTER_APP_CHECK_TOKEN to sync values.';
      _notify();
      return;
    }

    _isSyncingCashToClear = true;
    _cashToClearSyncMessage = 'Syncing Cash-to-Clear values...';
    _notify();

    try {
      final session = await _cashToClearApi.createSession();
      final remoteItems = <String, CashToClearItemDto>{};
      final groups = _groupedResult.groups;
      final syncedItems = await Future.wait(
        groups.map(
          (group) => _cashToClearApi.addItem(
            sessionId: session.sessionId,
            label: group.displayLabel,
            condition: 'unknown',
          ),
        ),
      );

      for (var index = 0; index < groups.length; index++) {
        remoteItems[groups[index].id] = syncedItems[index];
      }

      final refreshed = await _cashToClearApi.getSession(session.sessionId);
      _remoteSessionId = refreshed.sessionId;
      _remoteItemsByGroupId
        ..clear()
        ..addAll(remoteItems);
      _moneyOnTableLowUsd = refreshed.moneyOnTableLowUsd;
      _moneyOnTableHighUsd = refreshed.moneyOnTableHighUsd;
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage = 'Cash-to-Clear values synced.';
      _notify();
      await _flushPendingRemoteDecisions();
    } catch (error) {
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage = 'Local mode: backend sync failed ($error).';
      _notify();
    }
  }

  Future<void> _recordRemoteDecision({
    required DetectionGroup group,
    required DecisionCategory category,
    String? note,
  }) async {
    final sessionId = _remoteSessionId;
    final remoteItem = _remoteItemsByGroupId[group.id];
    if (!_cashToClearApi.isConfigured) {
      return;
    }

    final pending = _PendingRemoteDecision(
      groupId: group.id,
      category: category,
      note: note,
    );

    if (sessionId == null || remoteItem == null) {
      _pendingRemoteDecisions.add(pending);
      _cashToClearSyncMessage =
          'Decision queued until Cash-to-Clear sync is ready.';
      _notify();
      return;
    }

    _isSyncingCashToClear = true;
    _cashToClearSyncMessage = 'Saving decision to Cash-to-Clear...';
    _notify();

    try {
      await _syncRemoteDecision(pending);
      final refreshed = await _cashToClearApi.getSession(sessionId);
      _moneyOnTableLowUsd = refreshed.moneyOnTableLowUsd;
      _moneyOnTableHighUsd = refreshed.moneyOnTableHighUsd;
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage = 'Decision synced.';
      _notify();
    } catch (error) {
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage =
          'Decision saved locally; backend sync failed ($error).';
      _notify();
    }
  }

  Future<void> _flushPendingRemoteDecisions() async {
    if (!_cashToClearApi.isConfigured || _pendingRemoteDecisions.isEmpty) {
      return;
    }

    final pending = List<_PendingRemoteDecision>.from(_pendingRemoteDecisions);
    _pendingRemoteDecisions.clear();

    _isSyncingCashToClear = true;
    _cashToClearSyncMessage = 'Syncing queued decisions...';
    _notify();

    var syncedCount = 0;
    try {
      for (final decision in pending) {
        if (_remoteItemsByGroupId[decision.groupId] == null) {
          _pendingRemoteDecisions.add(decision);
          continue;
        }
        await _syncRemoteDecision(decision);
        syncedCount++;
      }

      final sessionId = _remoteSessionId;
      final refreshed = sessionId == null
          ? null
          : await _cashToClearApi.getSession(sessionId);
      if (refreshed != null) {
        _moneyOnTableLowUsd = refreshed.moneyOnTableLowUsd;
        _moneyOnTableHighUsd = refreshed.moneyOnTableHighUsd;
      }
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage = _pendingRemoteDecisions.isEmpty
          ? 'Queued decisions synced.'
          : 'Some decisions are still queued for sync.';
      _notify();
    } catch (error) {
      final failed = pending.skip(syncedCount);
      for (final decision in failed) {
        if (!_pendingRemoteDecisions.any((p) =>
            p.groupId == decision.groupId && p.category == decision.category)) {
          _pendingRemoteDecisions.add(decision);
        }
      }
      _isSyncingCashToClear = false;
      _cashToClearSyncMessage =
          'Decision saved locally; queued sync failed ($error).';
      _notify();
    }
  }

  Future<void> _syncRemoteDecision(_PendingRemoteDecision decision) async {
    final sessionId = _remoteSessionId;
    final remoteItem = _remoteItemsByGroupId[decision.groupId];
    if (sessionId == null || remoteItem == null) {
      throw const CashToClearApiException('Remote session is not ready.');
    }

    await _cashToClearApi.recordDecision(
      sessionId: sessionId,
      itemId: remoteItem.itemId,
      category: decision.category,
      note: decision.note,
    );
  }

  void _notify() {
    if (!_disposed) {
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    if (_ownsCashToClearApi) {
      _cashToClearApi.dispose();
    }
    if (_ownsValuationService) {
      _valuationService.dispose();
    }
    super.dispose();
  }
}

class _PendingRemoteDecision {
  const _PendingRemoteDecision({
    required this.groupId,
    required this.category,
    this.note,
  });

  final String groupId;
  final DecisionCategory category;
  final String? note;
}
