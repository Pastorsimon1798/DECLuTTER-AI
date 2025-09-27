import 'dart:io' show File;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../grouping/domain/detection_group.dart';
import '../domain/session_decision.dart';
import 'widgets/focus_timer.dart';
import 'widgets/quick_start_card.dart';

class SessionTimerScreen extends StatefulWidget {
  const SessionTimerScreen({
    super.key,
    this.capturedImagePath,
    this.capturedAt,
    this.detectionGroups = const [],
  });

  final String? capturedImagePath;
  final DateTime? capturedAt;
  final List<DetectionGroup> detectionGroups;

  @override
  State<SessionTimerScreen> createState() => _SessionTimerScreenState();
}

class _SessionTimerScreenState extends State<SessionTimerScreen> {
  final List<SessionDecision> _decisions = [];
  String? _selectedGroupId;

  @override
  void initState() {
    super.initState();
    if (widget.detectionGroups.isNotEmpty) {
      _selectedGroupId = widget.detectionGroups.first.id;
    }
  }

  Future<void> _handleDecision(DecisionCategory category) async {
    final selectedGroup = _groupForId(_selectedGroupId);
    if (selectedGroup == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select a highlighted group before logging a decision.')),
      );
      return;
    }

    final note = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => _DecisionNoteSheet(
        category: category,
        group: selectedGroup,
        progress: _decisions.where((decision) => decision.groupId == selectedGroup.id).length,
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
  }

  DetectionGroup? _groupForId(String? id) {
    if (id == null) {
      return null;
    }
    for (final group in widget.detectionGroups) {
      if (group.id == id) {
        return group;
      }
    }
    return null;
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
            const SizedBox(height: 24),
            FocusTimer(onCompleted: _handleTimerCompleted),
            const SizedBox(height: 24),
            SessionDecisionComposer(
              groups: widget.detectionGroups,
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
              groups: widget.detectionGroups,
            ),
          ],
        ),
      ),
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
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              child: Image.file(
                File(imagePath),
                fit: BoxFit.cover,
                height: 180,
              ),
            )
          else
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('Preview not available on web build, but your capture is saved.'),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Captured zone snapshot',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
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

class SessionDecisionComposer extends StatelessWidget {
  const SessionDecisionComposer({
    super.key,
    required this.groups,
    required this.selectedGroupId,
    required this.onGroupSelected,
    required this.decisions,
    required this.onCategorySelected,
  });

  final List<DetectionGroup> groups;
  final String? selectedGroupId;
  final ValueChanged<String> onGroupSelected;
  final List<SessionDecision> decisions;
  final ValueChanged<DecisionCategory> onCategorySelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final Map<String, int> decisionCounts = {};
    for (final decision in decisions) {
      decisionCounts.update(decision.groupId, (value) => value + 1, ifAbsent: () => 1);
    }

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Log your decisions',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('Choose a highlighted group, then tap the bucket that matches your action. Add a quick note to lock it in.'),
            const SizedBox(height: 16),
            if (groups.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceVariant,
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
                style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: groups
                    .map(
                      (group) {
                        final resolved = decisionCounts[group.id] ?? 0;
                        final isSelected = group.id == selectedGroupId;
                        final label = '${group.displayLabel} · ${resolved}/${group.count} sorted';
                        return ChoiceChip(
                          selected: isSelected,
                          onSelected: (_) => onGroupSelected(group.id),
                          avatar: const Icon(Icons.layers_outlined),
                          label: Text(label),
                        );
                      },
                    )
                    .toList(),
              ),
              const SizedBox(height: 16),
            ],
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: DecisionCategory.values
                  .map(
                    (category) => FilledButton.tonalIcon(
                      onPressed: groups.isEmpty || selectedGroupId == null
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
    required this.groups,
  });

  final List<SessionDecision> decisions;
  final List<DetectionGroup> groups;

  @override
  Widget build(BuildContext context) {
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
              const Text('Each logged action drops into this running list so your summary writes itself.'),
              if (groups.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: groups
                      .map(
                        (group) => Chip(
                          avatar: const Icon(Icons.layers_outlined),
                          label: Text('${group.displayLabel}: 0/${group.count} sorted'),
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
      decisionCounts.update(decision.groupId, (value) => value + 1, ifAbsent: () => 1);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Session log',
          style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        if (groups.isNotEmpty)
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: groups
                .map(
                  (group) {
                    final resolved = decisionCounts[group.id] ?? 0;
                    return Chip(
                      avatar: const Icon(Icons.assignment_turned_in_outlined),
                      label: Text('${group.displayLabel}: $resolved/${group.count} sorted'),
                    );
                  },
                )
                .toList(),
          ),
        if (groups.isNotEmpty) const SizedBox(height: 12),
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
                            color: decision.category.foregroundColor(theme.colorScheme),
                          ),
                          const SizedBox(width: 8),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                decision.category.label,
                                style: theme.textTheme.titleMedium?.copyWith(
                                  color: decision.category.foregroundColor(theme.colorScheme),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                'Group ${decision.groupId} • ${decision.groupLabel}',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: decision.category.foregroundColor(theme.colorScheme),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      Text(
                        TimeOfDay.fromDateTime(decision.createdAt).format(context),
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: decision.category.foregroundColor(theme.colorScheme),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Progress: ${decisionCounts[decision.groupId] ?? 0}/${decision.groupTotal} items sorted',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: decision.category.foregroundColor(theme.colorScheme),
                    ),
                  ),
                  if (decision.note != null && decision.note!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      decision.note!,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: decision.category.foregroundColor(theme.colorScheme),
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
    final progressValue = widget.group.count == 0 ? 0.0 : resolved / widget.group.count;
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
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
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
                    backgroundColor: theme.colorScheme.surfaceVariant,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text('${resolved}/${widget.group.count} sorted'),
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
            decoration: const InputDecoration(
              labelText: 'What action did you take?',
              hintText: 'e.g. Boxed kids books for library drop-off',
              border: OutlineInputBorder(),
            ),
            onSubmitted: (_) => Navigator.of(context).pop(_controller.text.trim()),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton(
              onPressed: () => Navigator.of(context).pop(_controller.text.trim()),
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
            style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          const Text('• Log your decisions for each highlighted group.'),
          const SizedBox(height: 8),
          const Text('• If something feels sticky, tap Maybe and move on.'),
          const SizedBox(height: 8),
          const Text('• Finish strong with the summary screen when you are ready.'),
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
