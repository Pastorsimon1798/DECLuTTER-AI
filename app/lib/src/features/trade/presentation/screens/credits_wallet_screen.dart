import 'package:flutter/material.dart';

import '../../models/trade_models.dart';
import '../../services/trade_service.dart';

class CreditsWalletScreen extends StatefulWidget {
  const CreditsWalletScreen({super.key});

  @override
  State<CreditsWalletScreen> createState() => _CreditsWalletScreenState();
}

class _CreditsWalletScreenState extends State<CreditsWalletScreen> {
  final _service = TradeService(baseUrl: 'https://kyanitelabs.tech/declutter');

  CreditBalance? _balance;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadBalance();
  }

  Future<void> _loadBalance() async {
    setState(() => _loading = true);
    try {
      final balance = await _service.getCreditBalance();
      setState(() {
        _balance = balance;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Credits Wallet'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadBalance,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadBalance,
              child: CustomScrollView(
                slivers: [
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(32),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF5D63FF), Color(0xFF8B5CF6)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              borderRadius: BorderRadius.circular(24),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(0xFF5D63FF).withOpacity(0.3),
                                  blurRadius: 20,
                                  offset: const Offset(0, 10),
                                ),
                              ],
                            ),
                            child: Column(
                              children: [
                                const Text(
                                  'BALANCE',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                    color: Colors.white70,
                                    letterSpacing: 2,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '${_balance?.balance.toStringAsFixed(0) ?? '0'}',
                                  style: const TextStyle(
                                    fontSize: 56,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                const Text(
                                  'credits',
                                  style: TextStyle(
                                    fontSize: 18,
                                    color: Colors.white70,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SliverToBoxAdapter(
                    child: Padding(
                      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                      child: Text(
                        'Transaction History',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  if (_balance?.transactions.isEmpty ?? true)
                    const SliverFillRemaining(
                      child: Center(child: Text('No transactions yet')),
                    )
                  else
                    SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          final tx = _balance!.transactions[index];
                          final isEarned = tx.direction == 'earned';
                          return ListTile(
                            leading: CircleAvatar(
                              backgroundColor: isEarned
                                  ? Colors.green.withOpacity(0.2)
                                  : Colors.red.withOpacity(0.2),
                              child: Icon(
                                isEarned ? Icons.arrow_downward : Icons.arrow_upward,
                                color: isEarned ? Colors.green : Colors.red,
                              ),
                            ),
                            title: Text(tx.itemLabel),
                            subtitle: Text(tx.createdAt.substring(0, 10)),
                            trailing: Text(
                              '${isEarned ? '+' : '-'}${tx.amount.toStringAsFixed(0)}',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: isEarned ? Colors.green : Colors.red,
                              ),
                            ),
                          );
                        },
                        childCount: _balance?.transactions.length ?? 0,
                      ),
                    ),
                ],
              ),
            ),
    );
  }
}
