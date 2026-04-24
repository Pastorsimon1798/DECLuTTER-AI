import 'dart:async';

import 'package:flutter/material.dart';

class FocusTimer extends StatefulWidget {
  const FocusTimer({super.key, this.onCompleted});

  final VoidCallback? onCompleted;

  @override
  State<FocusTimer> createState() => _FocusTimerState();
}

class _FocusTimerState extends State<FocusTimer> with WidgetsBindingObserver {
  static const _initialDuration = Duration(minutes: 10);
  late Duration _remaining = _initialDuration;
  Timer? _timer;
  bool _isRunning = false;
  DateTime? _backgroundedAt;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  DateTime? _timerTarget;

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    _timer = null;
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      if (_isRunning) {
        _backgroundedAt = DateTime.now();
        _timer?.cancel();
        _timer = null;
      }
    } else if (state == AppLifecycleState.resumed) {
      if (_backgroundedAt != null && _isRunning) {
        final elapsed = DateTime.now().difference(_backgroundedAt!);
        _backgroundedAt = null;
        if (!mounted) return;
        setState(() {
          _remaining = _remaining - elapsed;
          if (_remaining <= Duration.zero) {
            _remaining = Duration.zero;
            _isRunning = false;
            _timerTarget = null;
          }
        });
        if (_remaining > Duration.zero) {
          _startPeriodicTimer();
        } else {
          widget.onCompleted?.call();
        }
      }
    }
  }

  void _toggleTimer() {
    if (_isRunning) {
      _timer?.cancel();
      _timer = null;
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
      _timerTarget = DateTime.now().add(_remaining);
    });

    _startPeriodicTimer();
  }

  void _startPeriodicTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        _timer = null;
        return;
      }

      if (_timerTarget != null) {
        _remaining = _timerTarget!.difference(DateTime.now());
      }

      if (_remaining <= Duration.zero) {
        timer.cancel();
        _timer = null;
        setState(() {
          _isRunning = false;
          _remaining = Duration.zero;
          _timerTarget = null;
        });
        widget.onCompleted?.call();
        return;
      }

      setState(() {
        // _remaining is already updated above from target
      });
    });
  }

  void _resetTimer() {
    _timer?.cancel();
    _timer = null;
    _backgroundedAt = null;
    _timerTarget = null;
    setState(() {
      _remaining = _initialDuration;
      _isRunning = false;
    });
    FocusScope.of(context).unfocus();
  }

  @override
  Widget build(BuildContext context) {
    final minutes =
        _remaining.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds =
        _remaining.inSeconds.remainder(60).toString().padLeft(2, '0');

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
