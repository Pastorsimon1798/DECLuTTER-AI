import 'dart:io' show File;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../grouping/domain/detection_group.dart';
import '../../grouping/domain/grouped_detection_result.dart';
import '../domain/session_decision.dart';
import '../services/cash_to_clear_api.dart';
import 'widgets/focus_timer.dart';
import 'widgets/quick_start_card.dart';

class SessionTimerScreen extends StatefulWidget {
  const SessionTimerScreen({
    super.key,
    this.capturedImagePath,
    this.capturedAt,
    this.groupedResult = const GroupedDetectionResult.empty(),
    this.cashToClearApi,
  });

  final String? capturedImagePath;
  final DateTime? capturedAt;
  final GroupedDetectionResult groupedResult;
  final CashToClearApiClient? cashToClearApi;

  @override
  State<SessionTimerScreen> createState() => _SessionTimerScreenState();
}

class _SessionTimerScreenState extends State<SessionTimerScreen> {
  final List<SessionDecision> _decisions = [];
  final Map<String, CashToClearItemDto> _remoteItemsByGroupId = {};
  final Map<String, String> _publicListingUrlsByGroupId = {};
  final Set<String> _creatingListingPageGroupIds = {};
  final List<_PendingRemoteDecision> _pendingRemoteDecisions = [];
  String? _selectedGroupId;
  late final CashToClearApiClient _cashToClearApi;
  String? _remoteSessionId;
  double? _moneyOnTableLowUsd;
  double? _moneyOnTableHighUsd;
  bool _isSyncingCashToClear = false;
  String? _cashToClearSyncMessage;
  bool _ownsCashToClearApi = false;

  @override
  void initState() {
    super.initState();
    _ownsCashToClearApi = widget.cashToClearApi == null;
    _cashToClearApi =
        widget.cashToClearApi ?? CashToClearApiClient.fromEnvironment();
    if (widget.groupedResult.hasGroups) {
      _selectedGroupId = widget.groupedResult.primaryGroup?.id;
    }
    _bootstrapCashToClearSession();
  }

  @override
  void dispose() {
    if (_ownsCashToClearApi) {
      _cashToClearApi.dispose();
    }
    super.dispose();
  }

  Future<void> _bootstrapCashToClearSession() async {
    if (!_cashToClearApi.isConfigured || !widget.groupedResult.hasGroups) {
      _cashToClearSyncMessage = _cashToClearApi.isConfigured
          ? 'Cash-to-Clear backend is ready. Capture detections to sync values.'
          : 'Local mode: add DECLUTTER_API_BASE_URL, DECLUTTER_ID_TOKEN, and DECLUTTER_APP_CHECK_TOKEN to sync values.';
      return;
    }

    setState(() {
      _isSyncingCashToClear = true;
      _cashToClearSyncMessage = 'Syncing Cash-to-Clear values...';
    });

    try {
      final session = await _cashToClearApi.createSession();
      final remoteItems = <String, CashToClearItemDto>{};
      final groups = widget.groupedResult.groups;
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
      if (!mounted) return;
      setState(() {
        _remoteSessionId = refreshed.sessionId;
        _remoteItemsByGroupId
          ..clear()
          ..addAll(remoteItems);
        _moneyOnTableLowUsd = refreshed.moneyOnTableLowUsd;
        _moneyOnTableHighUsd = refreshed.moneyOnTableHighUsd;
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage = 'Cash-to-Clear values synced.';
      });
      await _flushPendingRemoteDecisions();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage = 'Local mode: backend sync failed ($error).';
      });
    }
  }

  Future<void> _handleDecision(DecisionCategory category) async {
    final selectedGroup = widget.groupedResult.groupForId(_selectedGroupId);
    if (selectedGroup == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content:
                Text('Select a highlighted group before logging a decision.')),
      );
      return;
    }

    final note = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => _DecisionNoteSheet(
        category: category,
        group: selectedGroup,
        progress: _decisions
            .where((decision) => decision.groupId == selectedGroup.id)
            .length,
      ),
    );

    if (!mounted || note == null) {
      return;
    }

    setState(() {
      _decisions.insert(
        0,
        SessionDecision(
          groupId: selectedGroup.id,
          groupLabel: selectedGroup.friendlyLabel,
          groupTotal: selectedGroup.count,
          category: category,
          createdAt: DateTime.now(),
          note: note.isEmpty ? null : note,
        ),
      );
    });

    await _recordRemoteDecision(
      group: selectedGroup,
      category: category,
      note: note.isEmpty ? null : note,
    );
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
      setState(() {
        _cashToClearSyncMessage =
            'Decision queued until Cash-to-Clear sync is ready.';
      });
      return;
    }

    setState(() {
      _isSyncingCashToClear = true;
      _cashToClearSyncMessage = 'Saving decision to Cash-to-Clear...';
    });

    try {
      await _syncRemoteDecision(pending);
      final refreshed = await _cashToClearApi.getSession(sessionId);
      if (!mounted) return;
      setState(() {
        _moneyOnTableLowUsd = refreshed.moneyOnTableLowUsd;
        _moneyOnTableHighUsd = refreshed.moneyOnTableHighUsd;
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage = 'Decision synced.';
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage =
            'Decision saved locally; backend sync failed ($error).';
      });
    }
  }

  Future<void> _flushPendingRemoteDecisions() async {
    if (!_cashToClearApi.isConfigured || _pendingRemoteDecisions.isEmpty) {
      return;
    }

    final pending = List<_PendingRemoteDecision>.from(_pendingRemoteDecisions);
    _pendingRemoteDecisions.clear();

    setState(() {
      _isSyncingCashToClear = true;
      _cashToClearSyncMessage = 'Syncing queued decisions...';
    });

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
      if (!mounted) return;
      setState(() {
        if (refreshed != null) {
          _moneyOnTableLowUsd = refreshed.moneyOnTableLowUsd;
          _moneyOnTableHighUsd = refreshed.moneyOnTableHighUsd;
        }
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage = _pendingRemoteDecisions.isEmpty
            ? 'Queued decisions synced.'
            : 'Some decisions are still queued for sync.';
      });
    } catch (error) {
      final failed = pending.skip(syncedCount);
      for (final decision in failed) {
        if (!_pendingRemoteDecisions.any((p) => p.groupId == decision.groupId && p.category == decision.category)) {
          _pendingRemoteDecisions.add(decision);
        }
      }
      if (!mounted) return;
      setState(() {
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage =
            'Decision saved locally; queued sync failed ($error).';
      });
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

  Future<void> _createPublicListingPage(String groupId) async {
    final sessionId = _remoteSessionId;
    final remoteItem = _remoteItemsByGroupId[groupId];
    if (!_cashToClearApi.isConfigured ||
        sessionId == null ||
        remoteItem == null) {
      setState(() {
        _cashToClearSyncMessage =
            'Sync Cash-to-Clear values before creating a page.';
      });
      return;
    }

    setState(() {
      _isSyncingCashToClear = true;
      _creatingListingPageGroupIds.add(groupId);
      _cashToClearSyncMessage = 'Creating standalone listing page...';
    });

    try {
      final listing = await _cashToClearApi.createPublicListing(
        sessionId: sessionId,
        itemId: remoteItem.itemId,
      );
      if (!mounted) return;
      setState(() {
        _publicListingUrlsByGroupId[groupId] = listing.publicUrl;
        _creatingListingPageGroupIds.remove(groupId);
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage = 'Standalone listing page created.';
      });
    } catch (error) {
      debugPrint('Cash-to-Clear public listing creation failed: $error');
      if (!mounted) return;
      setState(() {
        _creatingListingPageGroupIds.remove(groupId);
        _isSyncingCashToClear = false;
        _cashToClearSyncMessage =
            'Could not create listing page. Please try again.';
      });
    }
  }

  void _handleTimerCompleted() {
    if (!mounted) return;
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (_) => const _TimerCompleteSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('10-Min Declutter Sprint'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (widget.capturedImagePath != null)
              _CapturedPhotoPreview(
                imagePath: widget.capturedImagePath!,
                capturedAt: widget.capturedAt,
              ),
            const QuickStartCard(),
            const SizedBox(height: 16),
            CashToClearStatusCard(
              isSyncing: _isSyncingCashToClear,
              message: _cashToClearSyncMessage,
              moneyOnTableLowUsd: _moneyOnTableLowUsd,
              moneyOnTableHighUsd: _moneyOnTableHighUsd,
              remoteItemsByGroupId: _remoteItemsByGroupId,
              publicListingUrlsByGroupId: _publicListingUrlsByGroupId,
              creatingListingPageGroupIds: _creatingListingPageGroupIds,
              groupedResult: widget.groupedResult,
              onCreateListingPage: _createPublicListingPage,
            ),
            const SizedBox(height: 24),
            FocusTimer(onCompleted: _handleTimerCompleted),
            const SizedBox(height: 24),
            SessionDecisionComposer(
              groupedResult: widget.groupedResult,
              selectedGroupId: _selectedGroupId,
              onGroupSelected: (groupId) {
                setState(() => _selectedGroupId = groupId);
              },
              decisions: _decisions,
              onCategorySelected: _handleDecision,
            ),
            const SizedBox(height: 16),
            SessionDecisionHistory(
              decisions: _decisions,
              groupedResult: widget.groupedResult,
            ),
            const SizedBox(height: 16),
            SessionSummaryCard(
              decisions: _decisions,
              groupedResult: widget.groupedResult,
              moneyOnTableLowUsd: _moneyOnTableLowUsd,
              moneyOnTableHighUsd: _moneyOnTableHighUsd,
              publicListingUrlsByGroupId: _publicListingUrlsByGroupId,
            ),
          ],
        ),
      ),
    );
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

class _CapturedPhotoPreview extends StatelessWidget {
  const _CapturedPhotoPreview({required this.imagePath, this.capturedAt});

  final String imagePath;
  final DateTime? capturedAt;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (!kIsWeb)
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(12)),
              child: Image.file(
                File(imagePath),
                fit: BoxFit.cover,
                height: 180,
              ),
            )
          else
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                  'Preview not available on web build, but your capture is saved.'),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Captured zone snapshot',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                if (capturedAt != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Taken ${TimeOfDay.fromDateTime(capturedAt!).format(context)}',
                    style: theme.textTheme.bodySmall,
                  ),
                ],
                const SizedBox(height: 12),
                Text(
                  'Next up: the model will find clusters so you can move through Keep, Donate/Sell, Trash, Relocate, or Maybe decisions.',
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class CashToClearStatusCard extends StatelessWidget {
  const CashToClearStatusCard({
    super.key,
    required this.isSyncing,
    required this.message,
    required this.moneyOnTableLowUsd,
    required this.moneyOnTableHighUsd,
    required this.remoteItemsByGroupId,
    required this.publicListingUrlsByGroupId,
    required this.creatingListingPageGroupIds,
    required this.groupedResult,
    required this.onCreateListingPage,
  });

  final bool isSyncing;
  final String? message;
  final double? moneyOnTableLowUsd;
  final double? moneyOnTableHighUsd;
  final Map<String, CashToClearItemDto> remoteItemsByGroupId;
  final Map<String, String> publicListingUrlsByGroupId;
  final Set<String> creatingListingPageGroupIds;
  final GroupedDetectionResult groupedResult;
  final ValueChanged<String> onCreateListingPage;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasValue = moneyOnTableLowUsd != null && moneyOnTableHighUsd != null;
    final valueText = hasValue
        ? '\$${moneyOnTableLowUsd!.toStringAsFixed(0)}–${moneyOnTableHighUsd!.toStringAsFixed(0)}'
        : '—';

    return Card(
      elevation: 0,
      color: theme.colorScheme.secondaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.attach_money,
                    color: theme.colorScheme.onSecondaryContainer),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Money on the table',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: theme.colorScheme.onSecondaryContainer,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (isSyncing)
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              valueText,
              style: theme.textTheme.headlineMedium?.copyWith(
                color: theme.colorScheme.onSecondaryContainer,
                fontWeight: FontWeight.bold,
              ),
            ),
            if (message != null) ...[
              const SizedBox(height: 8),
              Text(
                message!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSecondaryContainer,
                ),
              ),
            ],
            if (remoteItemsByGroupId.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: groupedResult.groups.map((group) {
                  final item = remoteItemsByGroupId[group.id];
                  if (item == null) {
                    return Chip(label: Text('${group.displayLabel}: syncing'));
                  }
                  return Chip(
                    avatar: const Icon(Icons.sell_outlined),
                    label: Text(
                      '${group.displayLabel}: \$${item.valuation.lowUsd.toStringAsFixed(0)}–${item.valuation.highUsd.toStringAsFixed(0)}',
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 12),
              ...groupedResult.groups.map((group) {
                final item = remoteItemsByGroupId[group.id];
                if (item == null) {
                  return const SizedBox.shrink();
                }
                final publicUrl = publicListingUrlsByGroupId[group.id];
                final isCreating =
                    creatingListingPageGroupIds.contains(group.id);
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      OutlinedButton.icon(
                        onPressed: isCreating || publicUrl != null
                            ? null
                            : () => onCreateListingPage(group.id),
                        icon: Icon(
                            isCreating ? Icons.hourglass_empty : Icons.public),
                        label: Text(
                          isCreating
                              ? 'Creating page...'
                              : publicUrl == null
                                  ? 'Create page for ${group.displayLabel}'
                                  : 'Page created for ${group.displayLabel}',
                        ),
                      ),
                      if (publicUrl != null) ...[
                        const SizedBox(height: 4),
                        SelectableText(
                          publicUrl,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSecondaryContainer,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }
}

class SessionDecisionComposer extends StatelessWidget {
  const SessionDecisionComposer({
    super.key,
    required this.groupedResult,
    required this.selectedGroupId,
    required this.onGroupSelected,
    required this.decisions,
    required this.onCategorySelected,
  });

  final GroupedDetectionResult groupedResult;
  final String? selectedGroupId;
  final ValueChanged<String> onGroupSelected;
  final List<SessionDecision> decisions;
  final ValueChanged<DecisionCategory> onCategorySelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final Map<String, int> decisionCounts = {};
    for (final decision in decisions) {
      decisionCounts.update(decision.groupId, (value) => value + 1,
          ifAbsent: () => 1);
    }

    final groups = groupedResult.groups;

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Log your decisions',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
                'Choose a highlighted group, then tap the bucket that matches your action. Add a quick note to lock it in.'),
            const SizedBox(height: 16),
            if (!groupedResult.hasGroups)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'No grouped detections yet. Capture a zone photo or retry analysis to unlock guided sorting.',
                  textAlign: TextAlign.center,
                ),
              )
            else ...[
              Text(
                'Pick a group to work on:',
                style: theme.textTheme.bodyMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: groups.map(
                  (group) {
                    final resolved = decisionCounts[group.id] ?? 0;
                    final isSelected = group.id == selectedGroupId;
                    final label =
                        '${group.displayLabel} · $resolved/${group.count} sorted';
                    return ChoiceChip(
                      selected: isSelected,
                      onSelected: (_) => onGroupSelected(group.id),
                      avatar: const Icon(Icons.layers_outlined),
                      label: Text(label),
                    );
                  },
                ).toList(),
              ),
              const SizedBox(height: 16),
            ],
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: DecisionCategory.values
                  .map(
                    (category) => FilledButton.tonalIcon(
                      onPressed:
                          !groupedResult.hasGroups || selectedGroupId == null
                              ? null
                              : () => onCategorySelected(category),
                      icon: Icon(category.icon),
                      label: Text(category.label),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class SessionDecisionHistory extends StatelessWidget {
  const SessionDecisionHistory({
    super.key,
    required this.decisions,
    required this.groupedResult,
  });

  final List<SessionDecision> decisions;
  final GroupedDetectionResult groupedResult;

  @override
  Widget build(BuildContext context) {
    final groups = groupedResult.groups;
    if (decisions.isEmpty) {
      return Card(
        elevation: 0,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Decisions appear here',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                  'Each logged action drops into this running list so your summary writes itself.'),
              if (groupedResult.hasGroups) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: groups
                      .map(
                        (group) => Chip(
                          avatar: const Icon(Icons.layers_outlined),
                          label: Text(
                              '${group.displayLabel}: 0/${group.count} sorted'),
                        ),
                      )
                      .toList(),
                ),
              ],
            ],
          ),
        ),
      );
    }

    final theme = Theme.of(context);
    final Map<String, int> decisionCounts = {};
    for (final decision in decisions) {
      decisionCounts.update(decision.groupId, (value) => value + 1,
          ifAbsent: () => 1);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Session log',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        if (groupedResult.hasGroups)
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: groups.map(
              (group) {
                final resolved = decisionCounts[group.id] ?? 0;
                return Chip(
                  avatar: const Icon(Icons.assignment_turned_in_outlined),
                  label: Text(
                      '${group.displayLabel}: $resolved/${group.count} sorted'),
                );
              },
            ).toList(),
          ),
        if (groupedResult.hasGroups) const SizedBox(height: 12),
        ...decisions.map(
          (decision) => Card(
            margin: const EdgeInsets.only(bottom: 12),
            color: decision.category.containerColor(theme.colorScheme),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(
                            decision.category.icon,
                            color: decision.category
                                .foregroundColor(theme.colorScheme),
                          ),
                          const SizedBox(width: 8),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                decision.category.label,
                                style: theme.textTheme.titleMedium?.copyWith(
                                  color: decision.category
                                      .foregroundColor(theme.colorScheme),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                'Group ${decision.groupId} • ${decision.groupLabel}',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: decision.category
                                      .foregroundColor(theme.colorScheme),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      Text(
                        TimeOfDay.fromDateTime(decision.createdAt)
                            .format(context),
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: decision.category
                              .foregroundColor(theme.colorScheme),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Progress: ${decisionCounts[decision.groupId] ?? 0}/${decision.groupTotal} items sorted',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color:
                          decision.category.foregroundColor(theme.colorScheme),
                    ),
                  ),
                  if (decision.note != null && decision.note!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      decision.note!,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: decision.category
                            .foregroundColor(theme.colorScheme),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class SessionSummaryCard extends StatelessWidget {
  const SessionSummaryCard({
    super.key,
    required this.decisions,
    required this.groupedResult,
    required this.moneyOnTableLowUsd,
    required this.moneyOnTableHighUsd,
    required this.publicListingUrlsByGroupId,
  });

  final List<SessionDecision> decisions;
  final GroupedDetectionResult groupedResult;
  final double? moneyOnTableLowUsd;
  final double? moneyOnTableHighUsd;
  final Map<String, String> publicListingUrlsByGroupId;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final totalItems =
        groupedResult.groups.fold<int>(0, (sum, group) => sum + group.count);
    final decidedItems = decisions.length;
    final counts = <DecisionCategory, int>{
      for (final category in DecisionCategory.values) category: 0,
    };
    for (final decision in decisions) {
      counts.update(decision.category, (value) => value + 1, ifAbsent: () => 1);
    }
    final hasMoneyTotal =
        moneyOnTableLowUsd != null && moneyOnTableHighUsd != null;

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Sprint summary',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(totalItems == 0
                ? '$decidedItems decisions logged'
                : '$decidedItems/$totalItems items decided'),
            if (hasMoneyTotal) ...[
              const SizedBox(height: 8),
              Text(
                'Money still on the table: '
                '\$${moneyOnTableLowUsd!.toStringAsFixed(0)}–${moneyOnTableHighUsd!.toStringAsFixed(0)}',
                style: theme.textTheme.bodyMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: DecisionCategory.values
                  .where((category) => (counts[category] ?? 0) > 0)
                  .map(
                    (category) => Chip(
                      avatar: Icon(category.icon),
                      label: Text('${category.label}: ${counts[category]}'),
                    ),
                  )
                  .toList(),
            ),
            if (publicListingUrlsByGroupId.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Listing pages',
                style: theme.textTheme.bodyMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...publicListingUrlsByGroupId.entries.map(
                (entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: SelectableText(entry.value),
                ),
              ),
            ],
            if (decisions.isEmpty && publicListingUrlsByGroupId.isEmpty) ...[
              const SizedBox(height: 8),
              const Text(
                  'Log a decision or create a listing page to start your summary.'),
            ],
          ],
        ),
      ),
    );
  }
}

class _DecisionNoteSheet extends StatefulWidget {
  const _DecisionNoteSheet({
    required this.category,
    required this.group,
    required this.progress,
  });

  final DecisionCategory category;
  final DetectionGroup group;
  final int progress;

  @override
  State<_DecisionNoteSheet> createState() => _DecisionNoteSheetState();
}

class _DecisionNoteSheetState extends State<_DecisionNoteSheet> {
  late final TextEditingController _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final resolved = widget.progress;
    final remainingRaw = widget.group.count - resolved;
    final remaining = remainingRaw < 0 ? 0 : remainingRaw;
    final progressValue =
        widget.group.count == 0 ? 0.0 : resolved / widget.group.count;
    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
        top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(widget.category.icon),
              const SizedBox(width: 8),
              Text(
                widget.category.label,
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Group ${widget.group.id} • ${widget.group.friendlyLabel}',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(999),
                  child: LinearProgressIndicator(
                    value: progressValue.clamp(0.0, 1.0),
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text('$resolved/${widget.group.count} sorted'),
            ],
          ),
          if (remaining > 0) ...[
            const SizedBox(height: 4),
            Text(
              remaining == 1
                  ? 'One item left in this group after this note.'
                  : '$remaining items left in this group after this note.',
              style: theme.textTheme.bodySmall,
            ),
          ],
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            autofocus: true,
            textInputAction: TextInputAction.done,
            maxLines: 3,
            maxLength: 500,
            decoration: const InputDecoration(
              labelText: 'What action did you take?',
              hintText: 'e.g. Boxed kids books for library drop-off',
              border: OutlineInputBorder(),
            ),
            onSubmitted: (_) =>
                Navigator.of(context).pop(_controller.text.trim()),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton(
              onPressed: () =>
                  Navigator.of(context).pop(_controller.text.trim()),
              child: const Text('Save decision'),
            ),
          ),
        ],
      ),
    );
  }
}

class _TimerCompleteSheet extends StatelessWidget {
  const _TimerCompleteSheet();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Time! Celebrate the wins',
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          const Text('• Log your decisions for each highlighted group.'),
          const SizedBox(height: 8),
          const Text('• If something feels sticky, tap Maybe and move on.'),
          const SizedBox(height: 8),
          const Text(
              '• Finish strong with the summary screen when you are ready.'),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Back to sorting'),
            ),
          ),
        ],
      ),
    );
  }
}
