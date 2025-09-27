import 'package:flutter/material.dart';

enum DecisionCategory {
  keep,
  donate,
  trash,
  relocate,
  maybe,
}

extension DecisionCategoryX on DecisionCategory {
  String get label {
    switch (this) {
      case DecisionCategory.keep:
        return 'Keep';
      case DecisionCategory.donate:
        return 'Donate / Sell';
      case DecisionCategory.trash:
        return 'Trash';
      case DecisionCategory.relocate:
        return 'Relocate';
      case DecisionCategory.maybe:
        return 'Maybe';
    }
  }

  IconData get icon {
    switch (this) {
      case DecisionCategory.keep:
        return Icons.favorite_outline;
      case DecisionCategory.donate:
        return Icons.volunteer_activism_outlined;
      case DecisionCategory.trash:
        return Icons.delete_outline;
      case DecisionCategory.relocate:
        return Icons.switch_right;
      case DecisionCategory.maybe:
        return Icons.help_outline;
    }
  }

  Color containerColor(ColorScheme scheme) {
    switch (this) {
      case DecisionCategory.keep:
        return scheme.primaryContainer;
      case DecisionCategory.donate:
        return scheme.secondaryContainer;
      case DecisionCategory.trash:
        return scheme.errorContainer;
      case DecisionCategory.relocate:
        return scheme.tertiaryContainer;
      case DecisionCategory.maybe:
        return scheme.surfaceVariant;
    }
  }

  Color foregroundColor(ColorScheme scheme) {
    switch (this) {
      case DecisionCategory.keep:
        return scheme.onPrimaryContainer;
      case DecisionCategory.donate:
        return scheme.onSecondaryContainer;
      case DecisionCategory.trash:
        return scheme.onErrorContainer;
      case DecisionCategory.relocate:
        return scheme.onTertiaryContainer;
      case DecisionCategory.maybe:
        return scheme.onSurfaceVariant;
    }
  }
}

class SessionDecision {
  const SessionDecision({
    required this.groupId,
    required this.groupLabel,
    required this.groupTotal,
    required this.category,
    required this.createdAt,
    this.note,
  });

  final String groupId;
  final String groupLabel;
  final int groupTotal;
  final DecisionCategory category;
  final DateTime createdAt;
  final String? note;
}
