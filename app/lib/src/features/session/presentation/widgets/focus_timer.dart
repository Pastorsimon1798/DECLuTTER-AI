import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// A focus timer that persists its remaining duration across app lifecycle
/// changes and app restarts using [SharedPreferences].
class FocusTimer extends StatefulWidget {
  const FocusTimer({super.key, this.onCompleted});

  final VoidCallback? onCompleted;

  @override
  State<FocusTimer> createState() => _FocusTimerState();
}

class _FocusTimerState extends State<FocusTimer> with WidgetsBindingObserver {
  static const _initialDuration = Duration(minutes: 10);
  static const _prefsKeyPrefix = 'declutter_focus_timer';
  static const _prefsRemainingKey = '${_prefsKeyPrefix}_remaining_ms';
  static const _prefsTargetKey = '${_prefsKeyPrefix}_target_iso';
  static const _prefsIsRunningKey = '${_prefsKeyPrefix}_is_running';

  late Duration _remaining = _initialDuration;
  Timer? _timer;
  bool _isRunning = false;
  DateTime? _backgroundedAt;
  DateTime? _timerTarget;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_restoreTimerState());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    _timer = null;
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      if (_isRunning) {
        _backgroundedAt = DateTime.now();
        _timer?.cancel();
        _timer = null;
        unawaited(_persistTimerState());
      }
    } else if (state == AppLifecycleState.resumed) {
      if (_backgroundedAt != null && _isRunning) {
        final elapsed = DateTime.now().difference(_backgroundedAt!);
        _backgroundedAt = null;
        _remaining = _remaining - elapsed;
        if (_remaining <= Duration.zero) {
          _remaining = Duration.zero;
          _isRunning = false;
          _timerTarget = null;
          unawaited(_clearPersistedState());
          if (mounted) {
            setState(() {});
            widget.onCompleted?.call();
          }
          return;
        }
        if (mounted) {
          setState(() {});
          _startPeriodicTimer();
        }
      }
    }
  }

  Future<void> _persistTimerState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_prefsRemainingKey, _remaining.inMilliseconds);
      await prefs.setBool(_prefsIsRunningKey, _isRunning);
      if (_timerTarget != null) {
        await prefs.setString(_prefsTargetKey, _timerTarget!.toIso8601String());
      } else {
        await prefs.remove(_prefsTargetKey);
      }
    } catch (e) {
      debugPrint('FocusTimer: failed to persist state: $e');
    }
  }

  Future<void> _restoreTimerState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final remainingMs = prefs.getInt(_prefsRemainingKey);
      final isRunning = prefs.getBool(_prefsIsRunningKey) ?? false;
      final targetIso = prefs.getString(_prefsTargetKey);

      if (remainingMs == null) {
        return;
      }

      var remaining = Duration(milliseconds: remainingMs);
      DateTime? timerTarget;

      if (isRunning && targetIso != null) {
        timerTarget = DateTime.tryParse(targetIso);
        if (timerTarget != null) {
          final drift = DateTime.now().difference(timerTarget);
          remaining = remaining - drift;
        }
      }

      if (remaining <= Duration.zero) {
        remaining = Duration.zero;
        await _clearPersistedState();
        if (mounted) {
          setState(() {
            _remaining = remaining;
            _isRunning = false;
            _timerTarget = null;
          });
        }
        return;
      }

      if (!mounted) return;
      setState(() {
        _remaining = remaining;
        _isRunning = isRunning;
        _timerTarget = timerTarget;
      });

      if (isRunning && timerTarget != null) {
        _startPeriodicTimer();
      }
    } catch (e) {
      debugPrint('FocusTimer: failed to restore state: $e');
    }
  }

  Future<void> _clearPersistedState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_prefsRemainingKey);
      await prefs.remove(_prefsIsRunningKey);
      await prefs.remove(_prefsTargetKey);
    } catch (e) {
      debugPrint('FocusTimer: failed to clear persisted state: $e');
    }
  }

  void _toggleTimer() {
    if (_isRunning) {
      _timer?.cancel();
      _timer = null;
      setState(() {
        _isRunning = false;
      });
      unawaited(_persistTimerState());
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

    unawaited(_persistTimerState());
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
        unawaited(_clearPersistedState());
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
    unawaited(_clearPersistedState());
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
                Semantics(
                  button: true,
                  label: _isRunning ? 'Pause timer' : 'Start timer',
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(
                      minWidth: 48,
                      minHeight: 48,
                    ),
                    child: ElevatedButton.icon(
                      onPressed: _toggleTimer,
                      icon: Icon(_isRunning ? Icons.pause : Icons.play_arrow),
                      label: Text(_isRunning ? 'Pause' : 'Start'),
                      style: ElevatedButton.styleFrom(
                        minimumSize: const Size(48, 48),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Semantics(
                  button: true,
                  label: 'Reset timer',
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(
                      minWidth: 48,
                      minHeight: 48,
                    ),
                    child: TextButton.icon(
                      onPressed: _resetTimer,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Reset'),
                      style: TextButton.styleFrom(
                        minimumSize: const Size(48, 48),
                      ),
                    ),
                  ),
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
