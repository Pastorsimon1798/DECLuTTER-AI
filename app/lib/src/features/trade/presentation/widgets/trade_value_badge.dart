import 'package:flutter/material.dart';

class TradeValueBadge extends StatelessWidget {
  final double value;
  final bool showLabel;

  const TradeValueBadge({
    super.key,
    required this.value,
    this.showLabel = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF5D63FF).withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF5D63FF)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.token,
            size: 16,
            color: Color(0xFF5D63FF),
          ),
          const SizedBox(width: 4),
          Text(
            '${value.toStringAsFixed(0)}${showLabel ? ' credits' : ''}',
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Color(0xFF5D63FF),
            ),
          ),
        ],
      ),
    );
  }
}
