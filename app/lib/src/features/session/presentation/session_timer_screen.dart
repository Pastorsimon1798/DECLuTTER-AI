import 'dart:io' show File;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../decide/presentation/decision_card.dart';
import '../../grouping/domain/grouped_detection_result.dart';
import '../../valuate/models/valuation.dart';
import '../../summary/presentation/session_summary_screen.dart';
import '../domain/session_decision.dart';
import '../services/cash_to_clear_api.dart';
import 'session_controller.dart';
import 'session_state.dart';
import 'widgets/focus_timer.dart';
import 'widgets/quick_start_card.dart';

class SessionTimerScreen extends StatefulWidget {
  const SessionTimerScreen({
    super.key,
    this.capturedImagePath,
    this.capturedAt,
    this.groupedResult = const GroupedDetectionResult.empty(),
    this.controller,
  });

  final String? capturedImagePath;
  final DateTime? capturedAt;
  final GroupedDetectionResult groupedResult;
  final SessionController? controller;

  @override
  State<SessionTimerScreen> createState() => _SessionTimerScreenState();
}

class _SessionTimerScreenState extends State<SessionTimerScreen> {
  late final SessionController _controller;
  bool _ownsController = false;
  DateTime? _sessionStartTime;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller = widget.controller ??
        SessionController(
          groupedResult: widget.groupedResult,
        );
    _sessionStartTime = DateTime.now();
  }

  @override
  void dispose() {
    if (_ownsController) {
      _controller.dispose();
    }
    super.dispose();
  }

  void _handleTimerCompleted() {
    _controller.completeSprint();
    _navigateToSummary();
  }

  void _handleFinishSprint() {
    _controller.completeSprint();
    _navigateToSummary();
  }

  void _navigateToSummary() {
    if (!mounted) return;
    final state = _controller.state;
    final activeState = state is SessionActive ? state : null;
    if (activeState == null) return;

    final decisionsMap = <String, SessionDecision>{};
    for (final decision in activeState.decisions) {
      decisionsMap.putIfAbsent(decision.groupId, () => decision);
    }

    final valuationsMap = <String, Valuation?>{};
    for (final group in activeState.groupedResult.groups) {
      final remoteItem = activeState.remoteItemsByGroupId[group.id];
      final dto = remoteItem?.valuation;
      if (dto != null) {
        valuationsMap[group.id] = Valuation(
          low: dto.lowUsd,
          mid: (dto.lowUsd + dto.highUsd) / 2,
          high: dto.highUsd,
          confidence: double.tryParse(dto.confidence) ?? 0.3,
        );
      } else {
        valuationsMap[group.id] = null;
      }
    }

    final duration = _sessionStartTime != null
        ? DateTime.now().difference(_sessionStartTime!)
        : Duration.zero;

    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => SessionSummaryScreen(
          groupedResult: activeState.groupedResult,
          decisions: decisionsMap,
          valuations: valuationsMap,
          sessionDuration: duration,
          onStartNewSprint: () {
            Navigator.of(context).pop();
            setState(() {
              _sessionStartTime = DateTime.now();
            });
            _controller.resetSprint();
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _controller,
      builder: (context, _) {
        final state = _controller.state;
        final activeState = state is SessionActive ? state : null;

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
                if (activeState != null)
                  CashToClearStatusCard(
                    isSyncing: activeState.isSyncingCashToClear,
                    message: activeState.cashToClearSyncMessage,
                    moneyOnTableLowUsd: activeState.moneyOnTableLowUsd,
                    moneyOnTableHighUsd: activeState.moneyOnTableHighUsd,
                    remoteItemsByGroupId: activeState.remoteItemsByGroupId,
                    publicListingUrlsByGroupId:
                        activeState.publicListingUrlsByGroupId,
                    creatingListingPageGroupIds:
                        activeState.creatingListingPageGroupIds,
                    groupedResult: activeState.groupedResult,
                    onCreateListingPage: _controller.createPublicListingPage,
                  ),
                const SizedBox(height: 24),
                FocusTimer(onCompleted: _handleTimerCompleted),
                const SizedBox(height: 24),
                if (activeState != null &&
                    activeState.groupedResult.hasGroups) ...[
                  _SprintProgressHeader(
                    decidedCount: activeState.decidedCount,
                    totalCount: activeState.groupedResult.groupCount,
                  ),
                  const SizedBox(height: 16),
                  ...activeState.groupedResult.groups.map((group) {
                    final decision = _controller.decisionForGroup(group.id);
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: DecisionCard(
                        groupId: group.id,
                        groupLabel: group.displayLabel,
                        itemCount: group.count,
                        decision: decision,
                        valuation: activeState.valuationForGroup(group.id),
                        isLoadingValuation:
                            activeState.isValuationLoading(group.id),
                        onRetryValuation: () =>
                            _controller.retryValuation(group.id),
                        onDecision: (category, note) {
                          _controller.addDecision(
                            group.id,
                            category,
                            note: note,
                          );
                          HapticFeedback.lightImpact();
                        },
                        onUndo: () => _controller.undoDecision(group.id),
                      ),
                    );
                  }),
                  if (activeState.allGroupsDecided) ...[
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _handleFinishSprint,
                      child: const Text('Finish Sprint'),
                    ),
                  ],
                ] else if (activeState != null) ...[
                  Card(
                    elevation: 0,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        'No grouped detections yet. Capture a zone photo or retry analysis to unlock guided sorting.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                if (activeState != null)
                  SessionDecisionHistory(
                    decisions: activeState.decisions,
                    groupedResult: activeState.groupedResult,
                  ),
                const SizedBox(height: 16),
                if (activeState != null)
                  SessionSummaryCard(
                    decisions: activeState.decisions,
                    groupedResult: activeState.groupedResult,
                    moneyOnTableLowUsd: activeState.moneyOnTableLowUsd,
                    moneyOnTableHighUsd: activeState.moneyOnTableHighUsd,
                    publicListingUrlsByGroupId:
                        activeState.publicListingUrlsByGroupId,
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
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
                errorBuilder: (context, error, stackTrace) => Container(
                  height: 180,
                  alignment: Alignment.center,
                  padding: const EdgeInsets.all(16),
                  child: const Text(
                    'Photo preview unavailable. The captured file may have been removed by the system.',
                    textAlign: TextAlign.center,
                  ),
                ),
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

class _SprintProgressHeader extends StatelessWidget {
  const _SprintProgressHeader({
    required this.decidedCount,
    required this.totalCount,
  });

  final int decidedCount;
  final int totalCount;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: LinearProgressIndicator(
              value: totalCount == 0 ? 0 : decidedCount / totalCount,
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          '$decidedCount/$totalCount groups decided',
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
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
                    (category) => Semantics(
                      button: true,
                      label: '${category.label} decision',
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(
                          minWidth: 48,
                          minHeight: 48,
                        ),
                        child: FilledButton.tonalIcon(
                          onPressed:
                              !groupedResult.hasGroups || selectedGroupId == null
                                  ? null
                                  : () => onCategorySelected(category),
                          icon: Icon(category.icon),
                          label: Text(category.label),
                          style: FilledButton.styleFrom(
                            minimumSize: const Size(48, 48),
                          ),
                        ),
                      ),
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


