import 'package:flutter/material.dart';

import '../../grouping/domain/grouped_detection_result.dart';
import '../../session/domain/session_decision.dart';
import '../models/session_summary_data.dart';
import '../../valuate/models/valuation.dart';
import '../services/csv_export_service.dart';

/// Post-sprint review screen showing stats, group details, and CSV export.
class SessionSummaryScreen extends StatelessWidget {
  const SessionSummaryScreen({
    super.key,
    required this.groupedResult,
    required this.decisions,
    required this.valuations,
    required this.sessionDuration,
    this.onStartNewSprint,
  });

  final GroupedDetectionResult groupedResult;
  final Map<String, SessionDecision> decisions;
  final Map<String, Valuation?> valuations;
  final Duration sessionDuration;
  final VoidCallback? onStartNewSprint;

  SessionSummaryData get _data => SessionSummaryData(
        groupedResult: groupedResult,
        decisions: decisions,
        valuations: valuations,
        duration: sessionDuration,
      );

  String get _formattedDuration {
    final minutes = sessionDuration.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = sessionDuration.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final data = _data;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sprint Summary'),
        centerTitle: true,
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _Header(
              duration: _formattedDuration,
              totalDecided: data.totalItemsDecided,
            ),
            const SizedBox(height: 24),
            _StatsGrid(data: data),
            const SizedBox(height: 24),
            _ResaleValueCard(value: data.totalResaleValue),
            const SizedBox(height: 24),
            Text(
              'Groups',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            _GroupList(data: data),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => _onExportCsv(context, data),
              icon: const Icon(Icons.download),
              label: const Text('Export CSV'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => _onStartNewSprint(context),
              icon: const Icon(Icons.refresh),
              label: const Text('Start New Sprint'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _onExportCsv(BuildContext context, SessionSummaryData data) async {
    final csv = CsvExportService.generateCsv(data);
    final timestamp = DateTime.now().toIso8601String().replaceAll(':', '-');
    await CsvExportService.shareCsv(csv, 'declutter_sprint_$timestamp.csv');
  }

  void _onStartNewSprint(BuildContext context) {
    if (onStartNewSprint != null) {
      onStartNewSprint!();
    } else {
      Navigator.of(context).pop();
    }
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.duration, required this.totalDecided});

  final String duration;
  final int totalDecided;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Sprint Complete! 🎉',
          style: theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'You sorted $totalDecided ${totalDecided == 1 ? 'item' : 'items'} in $duration.',
          style: theme.textTheme.bodyLarge,
        ),
      ],
    );
  }
}

class _StatsGrid extends StatelessWidget {
  const _StatsGrid({required this.data});

  final SessionSummaryData data;

  @override
  Widget build(BuildContext context) {
    final stats = [
      _Stat(label: 'Keep', value: data.keepCount, icon: Icons.favorite_outline),
      _Stat(
        label: 'Donate',
        value: data.donateCount,
        icon: Icons.volunteer_activism_outlined,
      ),
      _Stat(label: 'Trash', value: data.trashCount, icon: Icons.delete_outline),
      _Stat(
        label: 'Relocate',
        value: data.relocateCount,
        icon: Icons.switch_right,
      ),
      _Stat(label: 'Maybe', value: data.maybeCount, icon: Icons.help_outline),
    ];

    return GridView.count(
      crossAxisCount: 3,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.2,
      children: stats.map((stat) => _StatCard(stat: stat)).toList(),
    );
  }
}

class _Stat {
  const _Stat({required this.label, required this.value, required this.icon});

  final String label;
  final int value;
  final IconData icon;
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.stat});

  final _Stat stat;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(stat.icon, color: theme.colorScheme.primary),
            const SizedBox(height: 8),
            Text(
              stat.value.toString(),
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              stat.label,
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _ResaleValueCard extends StatelessWidget {
  const _ResaleValueCard({required this.value});

  final double value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      color: theme.colorScheme.secondaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Estimated resale value',
              style: theme.textTheme.titleMedium?.copyWith(
                color: theme.colorScheme.onSecondaryContainer,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '\$${value.toStringAsFixed(2)}',
              style: theme.textTheme.headlineMedium?.copyWith(
                color: theme.colorScheme.onSecondaryContainer,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Sum of mid estimates for Keep + Relocate items',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSecondaryContainer,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GroupList extends StatelessWidget {
  const _GroupList({required this.data});

  final SessionSummaryData data;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: data.groupedResult.groups.map((group) {
        final decision = data.decisions[group.id];
        final valuation = data.valuations[group.id];
        return _GroupTile(
          groupLabel: group.displayLabel,
          itemCount: group.count,
          decision: decision,
          valuation: valuation,
        );
      }).toList(),
    );
  }
}

class _GroupTile extends StatelessWidget {
  const _GroupTile({
    required this.groupLabel,
    required this.itemCount,
    this.decision,
    this.valuation,
  });

  final String groupLabel;
  final int itemCount;
  final SessionDecision? decision;
  final Valuation? valuation;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final category = decision?.category;

    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      color: category?.containerColor(theme.colorScheme),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '$groupLabel · $itemCount ${itemCount == 1 ? 'item' : 'items'}',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: category?.foregroundColor(theme.colorScheme),
                    ),
                  ),
                ),
                if (category != null)
                  Chip(
                    avatar: Icon(
                      category.icon,
                      color: category.foregroundColor(theme.colorScheme),
                    ),
                    label: Text(
                      category.label,
                      style: TextStyle(
                        color: category.foregroundColor(theme.colorScheme),
                      ),
                    ),
                    backgroundColor: category
                        .containerColor(theme.colorScheme)
                        .withValues(alpha: 0.5),
                  ),
              ],
            ),
            if (decision?.note != null && decision!.note!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                decision!.note!,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: category?.foregroundColor(theme.colorScheme),
                ),
              ),
            ],
            if (valuation != null) ...[
              const SizedBox(height: 8),
              Text(
                'Value: \$${valuation!.low.toStringAsFixed(0)}–'
                '${valuation!.high.toStringAsFixed(0)} '
                '(mid \$${valuation!.mid.toStringAsFixed(0)}, '
                '${(valuation!.confidence * 100).toStringAsFixed(0)}% confidence)',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: category?.foregroundColor(theme.colorScheme),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
