import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:declutter_ai/src/data/db/session_database.dart';
import 'package:declutter_ai/src/data/repositories/session_repository.dart';
import 'package:declutter_ai/src/features/grouping/domain/detection_group.dart';
import 'package:declutter_ai/src/features/grouping/domain/grouped_detection_result.dart';
import 'package:declutter_ai/src/features/session/domain/session_decision.dart';
import 'package:declutter_ai/src/features/valuate/models/valuation.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  setUp(() async {
    final directory = Directory.systemTemp.createTempSync();
    const channel = MethodChannel('plugins.flutter.io/path_provider');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'getApplicationDocumentsDirectory') {
        return directory.path;
      }
      return null;
    });
    await SessionDatabase.resetForTesting();
  });

  tearDown(() async {
    await SessionDatabase.close();
  });

  group('SessionRepository', () {
    test('save and list sessions', () async {
      final repo = SessionRepository();
      const groupedResult = GroupedDetectionResult(
        groups: [
          DetectionGroup(
            id: 'g1',
            rawLabel: 'books',
            displayLabel: 'books',
            detections: [],
          ),
        ],
        totalDetections: 0,
        originalSize: Size.zero,
        isMocked: false,
      );

      await repo.saveSession(
        id: 'sess_1',
        imagePath: '/tmp/photo.jpg',
        groupedResult: groupedResult,
        decisions: [
          SessionDecision(
            groupId: 'g1',
            groupLabel: 'books',
            groupTotal: 3,
            category: DecisionCategory.keep,
            createdAt: DateTime.now(),
          ),
        ],
        valuations: {
          'g1': const Valuation(low: 10, mid: 15, high: 20, confidence: 0.5),
        },
        moneyOnTableLowUsd: 10,
        moneyOnTableHighUsd: 20,
      );

      final sessions = await repo.listSessions();
      expect(sessions.length, 1);
      expect(sessions.first.id, 'sess_1');
      expect(sessions.first.totalItems, 0);
      expect(sessions.first.decidedCount, 1);
      expect(sessions.first.moneyOnTableLowUsd, 10);
    });

    test('delete session removes it', () async {
      final repo = SessionRepository();
      const groupedResult = GroupedDetectionResult.empty();

      await repo.saveSession(
        id: 'sess_2',
        groupedResult: groupedResult,
        decisions: const [],
        valuations: const {},
      );

      await repo.deleteSession('sess_2');
      final sessions = await repo.listSessions();
      expect(sessions.isEmpty, isTrue);
    });

    test('markCompleted sets completed_at', () async {
      final repo = SessionRepository();
      const groupedResult = GroupedDetectionResult.empty();

      await repo.saveSession(
        id: 'sess_3',
        groupedResult: groupedResult,
        decisions: const [],
        valuations: const {},
      );

      await repo.markCompleted('sess_3');
      final session = await repo.getSession('sess_3');
      expect(session, isNotNull);
      expect(session!.completedAt, isNotNull);
    });
  });
}
