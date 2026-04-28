import 'package:flutter/material.dart';

class ConditionBadge extends StatelessWidget {
  final String condition;
  final bool large;

  const ConditionBadge({
    super.key,
    required this.condition,
    this.large = false,
  });

  Color get _color {
    switch (condition.toLowerCase()) {
      case 'new':
        return Colors.green;
      case 'like_new':
        return Colors.lightGreen;
      case 'good':
        return Colors.blue;
      case 'fair':
        return Colors.orange;
      case 'for_parts':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData get _icon {
    switch (condition.toLowerCase()) {
      case 'new':
        return Icons.star;
      case 'like_new':
        return Icons.star_half;
      case 'good':
        return Icons.thumb_up;
      case 'fair':
        return Icons.warning_amber;
      case 'for_parts':
        return Icons.build;
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = large ? 16.0 : 12.0;
    return Chip(
      avatar: Icon(_icon, size: size, color: Colors.white),
      label: Text(
        condition.toUpperCase(),
        style: TextStyle(
          fontSize: large ? 14 : 11,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      ),
      backgroundColor: _color,
      padding: EdgeInsets.symmetric(horizontal: large ? 12 : 6, vertical: large ? 6 : 2),
    );
  }
}
