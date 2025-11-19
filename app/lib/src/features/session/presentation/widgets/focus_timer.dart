import 'dart:async';

import 'package:flutter/material.dart';

class FocusTimer extends StatefulWidget {
  const FocusTimer({super.key, this.onCompleted});

  final VoidCallback? onCompleted;

  @override
  State<FocusTimer> createState() => _FocusTimerState();
}

class _FocusTimerState extends State<FocusTimer> {
  static const _initialDuration = Duration(minutes: 10);
  late Duration _remaining = _initialDuration;
  Timer? _timer;
  bool _isRunning = false;

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _toggleTimer() {
    if (_isRunning) {
      _timer?.cancel();
      setState(() {
        _isRunning = false;
      });
      return;
    }

    if (_remaining <= Duration.zero) {
      setState(() {
        _remaining = _initialDuration;
      });
    }

    setState(() {
      _isRunning = true;
    });

    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_remaining <= Duration.zero) {
        timer.cancel();
        if (!mounted) return;
        setState(() {
          _isRunning = false;
          _remaining = Duration.zero;
        });
        widget.onCompleted?.call();
        return;
      }

      if (!mounted) {
        timer.cancel();
        return;
      }

      setState(() {
        _remaining -= const Duration(seconds: 1);
      });
    });
  }

  void _resetTimer() {
    _timer?.cancel();
    setState(() {
      _remaining = _initialDuration;
      _isRunning = false;
    });
    FocusScope.of(context).unfocus();
  }

  @override
  Widget build(BuildContext context) {
    final minutes = _remaining.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = _remaining.inSeconds.remainder(60).toString().padLeft(2, '0');

    return Card(
      elevation: 0,
      color: Theme.of(context).colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Text(
              '$minutes:$seconds',
              style: Theme.of(context).textTheme.displayMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: _toggleTimer,
                  icon: Icon(_isRunning ? Icons.pause : Icons.play_arrow),
                  label: Text(_isRunning ? 'Pause' : 'Start'),
                ),
                const SizedBox(width: 12),
                TextButton.icon(
                  onPressed: _resetTimer,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reset'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Text(
              'Tip: When the timer ends, snap a photo and sort the highlighted groups.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
