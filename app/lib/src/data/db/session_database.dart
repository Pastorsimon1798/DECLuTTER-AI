import 'dart:async';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

/// Local SQLite persistence for declutter sessions, decisions, and valuations.
///
/// Uses sqflite so CI does not need build_runner (unlike drift).
class SessionDatabase {
  static Database? _db;

  static Future<Database> get database async {
    _db ??= await _open();
    return _db!;
  }

  static Future<Database> _open() async {
    final docsDir = await getApplicationDocumentsDirectory();
    final path = join(docsDir.path, 'declutter_sessions.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            image_path TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            money_on_table_low_usd REAL,
            money_on_table_high_usd REAL
          )
        ''');
        await db.execute('''
          CREATE TABLE session_groups (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            label TEXT NOT NULL,
            item_count INTEGER NOT NULL DEFAULT 1,
            average_confidence REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
          )
        ''');
        await db.execute('''
          CREATE TABLE session_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES session_groups(id) ON DELETE CASCADE
          )
        ''');
        await db.execute('''
          CREATE TABLE session_valuations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            low_usd REAL,
            mid_usd REAL,
            high_usd REAL,
            confidence REAL,
            source TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES session_groups(id) ON DELETE CASCADE
          )
        ''');
        await db.execute('''
          CREATE INDEX idx_groups_session ON session_groups(session_id)
        ''');
        await db.execute('''
          CREATE INDEX idx_decisions_session ON session_decisions(session_id)
        ''');
        await db.execute('''
          CREATE INDEX idx_valuations_session ON session_valuations(session_id)
        ''');
      },
    );
  }

  static Future<void> close() async {
    await _db?.close();
    _db = null;
  }

  static Future<void> resetForTesting() async {
    await close();
    final docsDir = await getApplicationDocumentsDirectory();
    final path = join(docsDir.path, 'declutter_sessions.db');
    await deleteDatabase(path);
  }
}
