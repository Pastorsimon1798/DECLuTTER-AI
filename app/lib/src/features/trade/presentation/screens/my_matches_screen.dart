import 'package:flutter/material.dart';

import '../../models/trade_models.dart';
import '../../services/trade_service.dart';

class MyMatchesScreen extends StatefulWidget {
  const MyMatchesScreen({super.key});

  @override
  State<MyMatchesScreen> createState() => _MyMatchesScreenState();
}

class _MyMatchesScreenState extends State<MyMatchesScreen>
    with SingleTickerProviderStateMixin {
  final _service = TradeService(baseUrl: 'https://kyanitelabs.tech/declutter');
  late TabController _tabController;

  List<TradeMatch> _incoming = [];
  List<TradeMatch> _outgoing = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadMatches();
  }

  Future<void> _loadMatches() async {
    setState(() => _loading = true);
    // Placeholder: in a real app, fetch from /trade/matches endpoint
    await Future.delayed(const Duration(milliseconds: 500));
    setState(() => _loading = false);
  }

  Future<void> _accept(TradeMatch match) async {
    try {
      await _service.acceptTrade(match.id);
      _loadMatches();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Trade accepted!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  Future<void> _decline(TradeMatch match) async {
    try {
      await _service.declineTrade(match.id);
      _loadMatches();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Trade declined')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Matches'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Incoming', icon: Icon(Icons.inbox)),
            Tab(text: 'Outgoing', icon: Icon(Icons.outbox)),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _MatchList(
                  matches: _incoming,
                  isIncoming: true,
                  onAccept: _accept,
                  onDecline: _decline,
                ),
                _MatchList(
                  matches: _outgoing,
                  isIncoming: false,
                  onAccept: null,
                  onDecline: null,
                ),
              ],
            ),
    );
  }
}

class _MatchList extends StatelessWidget {
  final List<TradeMatch> matches;
  final bool isIncoming;
  final ValueChanged<TradeMatch>? onAccept;
  final ValueChanged<TradeMatch>? onDecline;

  const _MatchList({
    required this.matches,
    required this.isIncoming,
    this.onAccept,
    this.onDecline,
  });

  Color _statusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'accepted':
      case 'completed':
        return Colors.green;
      case 'declined':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (matches.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isIncoming ? Icons.inbox_outlined : Icons.outbox_outlined,
              size: 64,
              color: Colors.grey.shade400,
            ),
            const SizedBox(height: 16),
            Text(
              isIncoming ? 'No incoming proposals' : 'No outgoing proposals',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: matches.length,
      itemBuilder: (context, index) {
        final match = matches[index];
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Chip(
                      label: Text(match.status.toUpperCase()),
                      backgroundColor: _statusColor(match.status).withOpacity(0.2),
                      side: BorderSide(color: _statusColor(match.status)),
                    ),
                    const Spacer(),
                    if (match.useCredits)
                      Chip(
                        label: Text('+${match.creditAmount.toStringAsFixed(0)} credits'),
                        backgroundColor: const Color(0xFF5D63FF).withOpacity(0.1),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  isIncoming
                      ? 'From: ${match.requesterId}'
                      : 'To: ${match.ownerId}',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                ),
                if (match.message.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      match.message,
                      style: const TextStyle(fontSize: 14, fontStyle: FontStyle.italic),
                    ),
                  ),
                ],
                if (isIncoming && match.status == 'pending') ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton(
                          onPressed: () => onAccept?.call(match),
                          child: const Text('Accept'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => onDecline?.call(match),
                          child: const Text('Decline'),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}
