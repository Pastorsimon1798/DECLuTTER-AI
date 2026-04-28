import 'package:sqflite/sqflite.dart';

import '../db/session_database.dart';
import '../../features/grouping/domain/grouped_detection_result.dart';
import '../../features/session/domain/session_decision.dart';
import '../../features/valuate/models/valuation.dart';

/// Plain data object for a persisted session read from SQLite.
class PersistedSession {
  const PersistedSession({
    required this.id,
    required this.imagePath,
    required this.createdAt,
    this.completedAt,
    required this.groups,
    required this.decisions,
    required this.valuations,
    this.moneyOnTableLowUsd,
    this.moneyOnTableHighUsd,
  });

  final String id;
  final String? imagePath;
  final DateTime createdAt;
  final DateTime? completedAt;
  final List<PersistedGroup> groups;
  final List<PersistedDecision> decisions;
  final List<PersistedValuation> valuations;
  final double? moneyOnTableLowUsd;
  final double? moneyOnTableHighUsd;

  int get decidedCount {
    final decidedIds = <String>{};
    for (final d in decisions) {
      decidedIds.add(d.groupId);
    }
    return decidedIds.length;
  }

  int get totalItems => groups.fold<int>(0, (sum, g) => sum + g.itemCount);
}

class PersistedGroup {
  const PersistedGroup({
    required this.id,
    required this.sessionId,
    required this.label,
    required this.itemCount,
    required this.averageConfidence,
    required this.createdAt,
  });

  final String id;
  final String sessionId;
  final String label;
  final int itemCount;
  final double averageConfidence;
  final DateTime createdAt;
}

class PersistedDecision {
  const PersistedDecision({
    required this.id,
    required this.sessionId,
    required this.groupId,
    required this.category,
    this.note,
    required this.createdAt,
  });

  final int id;
  final String sessionId;
  final String groupId;
  final String category;
  final String? note;
  final DateTime createdAt;
}

class PersistedValuation {
  const PersistedValuation({
    required this.id,
    required this.sessionId,
    required this.groupId,
    required this.lowUsd,
    required this.midUsd,
    required this.highUsd,
    required this.confidence,
    this.source,
    required this.createdAt,
  });

  final int id;
  final String sessionId;
  final String groupId;
  final double lowUsd;
  final double midUsd;
  final double highUsd;
  final double confidence;
  final String? source;
  final DateTime createdAt;
}

/// Repository for local session persistence.
class SessionRepository {
  Future<Database> get _db async => SessionDatabase.database;

  Future<void> saveSession({
    required String id,
    String? imagePath,
    required GroupedDetectionResult groupedResult,
    required List<SessionDecision> decisions,
    required Map<String, Valuation?> valuations,
    double? moneyOnTableLowUsd,
    double? moneyOnTableHighUsd,
  }) async {
    final db = await _db;
    final now = DateTime.now().toIso8601String();

    await db.transaction((txn) async {
      await txn.insert(
        'sessions',
        {
          'id': id,
          'image_path': imagePath,
          'created_at': now,
          'money_on_table_low_usd': moneyOnTableLowUsd,
          'money_on_table_high_usd': moneyOnTableHighUsd,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );

      for (final group in groupedResult.groups) {
        await txn.insert(
          'session_groups',
          {
            'id': group.id,
            'session_id': id,
            'label': group.displayLabel,
            'item_count': group.count,
            'average_confidence': group.averageConfidence,
            'created_at': now,
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      await txn.delete(
        'session_decisions',
        where: 'session_id = ?',
        whereArgs: [id],
      );
      for (final decision in decisions) {
        await txn.insert('session_decisions', {
          'session_id': id,
          'group_id': decision.groupId,
          'category': decision.category.name,
          'note': decision.note,
          'created_at': decision.createdAt.toIso8601String(),
        });
      }

      await txn.delete(
        'session_valuations',
        where: 'session_id = ?',
        whereArgs: [id],
      );
      for (final entry in valuations.entries) {
        final v = entry.value;
        if (v == null) continue;
        await txn.insert('session_valuations', {
          'session_id': id,
          'group_id': entry.key,
          'low_usd': v.low,
          'mid_usd': v.mid,
          'high_usd': v.high,
          'confidence': v.confidence,
          'source': 'local',
          'created_at': now,
        });
      }
    });
  }

  Future<List<PersistedSession>> listSessions() async {
    final db = await _db;
    final sessionRows = await db.query(
      'sessions',
      orderBy: 'created_at DESC',
    );

    final sessions = <PersistedSession>[];
    for (final row in sessionRows) {
      final id = row['id'] as String;
      sessions.add(await _hydrateSession(db, id, row));
    }
    return sessions;
  }

  Future<PersistedSession?> getSession(String id) async {
    final db = await _db;
    final rows = await db.query(
      'sessions',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (rows.isEmpty) return null;
    return _hydrateSession(db, id, rows.first);
  }

  Future<void> deleteSession(String id) async {
    final db = await _db;
    await db.delete(
      'sessions',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> markCompleted(String id) async {
    final db = await _db;
    await db.update(
      'sessions',
      {'completed_at': DateTime.now().toIso8601String()},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<PersistedSession> _hydrateSession(
    Database db,
    String id,
    Map<String, Object?> row,
  ) async {
    final groupRows = await db.query(
      'session_groups',
      where: 'session_id = ?',
      whereArgs: [id],
    );
    final decisionRows = await db.query(
      'session_decisions',
      where: 'session_id = ?',
      whereArgs: [id],
    );
    final valuationRows = await db.query(
      'session_valuations',
      where: 'session_id = ?',
      whereArgs: [id],
    );

    return PersistedSession(
      id: id,
      imagePath: row['image_path'] as String?,
      createdAt: DateTime.parse(row['created_at'] as String),
      completedAt: row['completed_at'] != null
          ? DateTime.parse(row['completed_at'] as String)
          : null,
      moneyOnTableLowUsd: row['money_on_table_low_usd'] as double?,
      moneyOnTableHighUsd: row['money_on_table_high_usd'] as double?,
      groups: groupRows.map((r) => PersistedGroup(
        id: r['id'] as String,
        sessionId: r['session_id'] as String,
        label: r['label'] as String,
        itemCount: r['item_count'] as int,
        averageConfidence: r['average_confidence'] as double,
        createdAt: DateTime.parse(r['created_at'] as String),
      )).toList(),
      decisions: decisionRows.map((r) => PersistedDecision(
        id: r['id'] as int,
        sessionId: r['session_id'] as String,
        groupId: r['group_id'] as String,
        category: r['category'] as String,
        note: r['note'] as String?,
        createdAt: DateTime.parse(r['created_at'] as String),
      )).toList(),
      valuations: valuationRows.map((r) => PersistedValuation(
        id: r['id'] as int,
        sessionId: r['session_id'] as String,
        groupId: r['group_id'] as String,
        lowUsd: r['low_usd'] as double,
        midUsd: r['mid_usd'] as double,
        highUsd: r['high_usd'] as double,
        confidence: r['confidence'] as double,
        source: r['source'] as String?,
        createdAt: DateTime.parse(r['created_at'] as String),
      )).toList(),
    );
  }
}
