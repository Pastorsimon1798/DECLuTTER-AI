import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:declutter_ai/src/features/session/domain/session_decision.dart';
import 'package:declutter_ai/src/features/valuate/models/valuation.dart';

/// A card that presents a single detection group and lets the user decide
/// its fate with large, ADHD-friendly action buttons.
class DecisionCard extends StatefulWidget {
  const DecisionCard({
    super.key,
    required this.groupId,
    required this.groupLabel,
    required this.itemCount,
    this.decision,
    this.valuation,
    this.isLoadingValuation = false,
    this.onRetryValuation,
    required this.onDecision,
    required this.onUndo,
  });

  final String groupId;
  final String groupLabel;
  final int itemCount;
  final SessionDecision? decision;
  final Valuation? valuation;
  final bool isLoadingValuation;
  final VoidCallback? onRetryValuation;
  final void Function(DecisionCategory category, String? note) onDecision;
  final VoidCallback onUndo;

  @override
  State<DecisionCard> createState() => _DecisionCardState();
}

class _DecisionCardState extends State<DecisionCard> {
  late final TextEditingController _noteController;
  bool _showRange = false;

  static const List<DecisionCategory> _categories = [
    DecisionCategory.keep,
    DecisionCategory.donate,
    DecisionCategory.trash,
    DecisionCategory.relocate,
    DecisionCategory.maybe,
  ];

  @override
  void initState() {
    super.initState();
    _noteController = TextEditingController(text: widget.decision?.note ?? '');
  }

  @override
  void didUpdateWidget(covariant DecisionCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    final newNote = widget.decision?.note ?? '';
    if (newNote != _noteController.text) {
      _noteController.text = newNote;
    }
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasDecision = widget.decision != null;

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header: thumbnail + label + count + value + undo
            Row(
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    Icons.layers_outlined,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${widget.groupLabel} · ${widget.itemCount} ${widget.itemCount == 1 ? 'item' : 'items'}',
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      _ValueRow(
                        isLoading: widget.isLoadingValuation,
                        valuation: widget.valuation,
                        showRange: _showRange,
                        onToggleRange: () => setState(() {
                          _showRange = !_showRange;
                        }),
                        onRetry: widget.onRetryValuation,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: hasDecision ? widget.onUndo : null,
                  icon: const Icon(Icons.undo),
                  tooltip: 'Undo decision',
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Action buttons
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _categories.map((category) {
                final isSelected = widget.decision?.category == category;
                return Semantics(
                  button: true,
                  label: '${category.label} decision',
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(
                      minWidth: 48,
                      minHeight: 48,
                    ),
                    child: FilledButton.tonalIcon(
                      onPressed: () {
                        HapticFeedback.lightImpact();
                        final note = _noteController.text.trim();
                        widget.onDecision(
                          category,
                          note.isEmpty ? null : note,
                        );
                      },
                      icon: Icon(category.icon),
                      label: Text(category.label),
                      style: FilledButton.styleFrom(
                        minimumSize: const Size(48, 48),
                        backgroundColor: isSelected
                            ? category.containerColor(theme.colorScheme)
                            : null,
                        foregroundColor: isSelected
                            ? category.foregroundColor(theme.colorScheme)
                            : null,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 12),
            // Note field
            TextField(
              controller: _noteController,
              decoration: const InputDecoration(
                hintText: 'Add a note (optional)',
                border: OutlineInputBorder(),
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              maxLines: 2,
              maxLength: 200,
              textInputAction: TextInputAction.done,
            ),
          ],
        ),
      ),
    );
  }
}

/// Displays the valuation text, loading spinner, or retry action.
class _ValueRow extends StatelessWidget {
  const _ValueRow({
    required this.isLoading,
    required this.valuation,
    required this.showRange,
    required this.onToggleRange,
    required this.onRetry,
  });

  final bool isLoading;
  final Valuation? valuation;
  final bool showRange;
  final VoidCallback onToggleRange;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (isLoading) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 12,
            height: 12,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            'Loading...',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      );
    }

    if (valuation != null) {
      final display = showRange
          ? '\$${valuation!.low.toStringAsFixed(0)}–${valuation!.high.toStringAsFixed(0)}'
          : '\$${valuation!.mid.toStringAsFixed(0)}';
      return GestureDetector(
        onTap: onToggleRange,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              display,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 4),
            Icon(
              showRange ? Icons.expand_less : Icons.expand_more,
              size: 14,
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ],
        ),
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'Est. value unavailable',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        if (onRetry != null) ...[
          const SizedBox(width: 6),
          InkWell(
            onTap: onRetry,
            child: Icon(
              Icons.refresh,
              size: 14,
              color: theme.colorScheme.primary,
            ),
          ),
        ],
      ],
    );
  }
}
