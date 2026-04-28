import 'package:flutter/material.dart';

import 'browse_trades_screen.dart';
import 'credits_wallet_screen.dart';
import 'my_listings_screen.dart';
import 'my_matches_screen.dart';

class TradeHubScreen extends StatefulWidget {
  const TradeHubScreen({super.key});

  @override
  State<TradeHubScreen> createState() => _TradeHubScreenState();
}

class _TradeHubScreenState extends State<TradeHubScreen> {
  int _currentIndex = 0;

  final _screens = const [
    BrowseTradesScreen(),
    MyMatchesScreen(),
    MyListingsScreen(),
    CreditsWalletScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            selectedIcon: Icon(Icons.explore),
            label: 'Browse',
          ),
          NavigationDestination(
            icon: Icon(Icons.swap_horiz_outlined),
            selectedIcon: Icon(Icons.swap_horiz),
            label: 'Matches',
          ),
          NavigationDestination(
            icon: Icon(Icons.inventory_2_outlined),
            selectedIcon: Icon(Icons.inventory_2),
            label: 'My Items',
          ),
          NavigationDestination(
            icon: Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(Icons.account_balance_wallet),
            label: 'Credits',
          ),
        ],
      ),
    );
  }
}
