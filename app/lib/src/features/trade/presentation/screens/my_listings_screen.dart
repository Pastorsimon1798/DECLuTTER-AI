import 'package:flutter/material.dart';

import '../../models/trade_models.dart';
import '../widgets/condition_badge.dart';
import '../widgets/trade_value_badge.dart';
import 'create_trade_listing_screen.dart';

class MyListingsScreen extends StatefulWidget {
  const MyListingsScreen({super.key});

  @override
  State<MyListingsScreen> createState() => _MyListingsScreenState();
}

class _MyListingsScreenState extends State<MyListingsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  List<TradeListing> _active = [];
  List<TradeListing> _pending = [];
  List<TradeListing> _completed = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadListings();
  }

  Future<void> _loadListings() async {
    setState(() => _loading = true);
    // Placeholder: in a real app, fetch from /trade/listings/my endpoint
    await Future.delayed(const Duration(milliseconds: 500));
    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Listings'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Active'),
            Tab(text: 'Pending'),
            Tab(text: 'Completed'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadListings,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _ListingList(listings: _active),
                _ListingList(listings: _pending),
                _ListingList(listings: _completed),
              ],
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const CreateTradeListingScreen()),
        ),
        icon: const Icon(Icons.add),
        label: const Text('New Listing'),
      ),
    );
  }
}

class _ListingList extends StatelessWidget {
  final List<TradeListing> listings;

  const _ListingList({required this.listings});

  @override
  Widget build(BuildContext context) {
    if (listings.isEmpty) {
      return const Center(child: Text('No listings'));
    }
    return ListView.builder(
      itemCount: listings.length,
      itemBuilder: (context, index) {
        final listing = listings[index];
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: listing.status == 'available'
                  ? Colors.green.shade100
                  : listing.status == 'pending'
                      ? Colors.orange.shade100
                      : Colors.grey.shade100,
              child: Icon(
                listing.status == 'available'
                    ? Icons.check
                    : listing.status == 'pending'
                        ? Icons.pending
                        : Icons.done_all,
                color: listing.status == 'available'
                    ? Colors.green
                    : listing.status == 'pending'
                        ? Colors.orange
                        : Colors.grey,
              ),
            ),
            title: Text(listing.itemLabel),
            subtitle: Row(
              children: [
                ConditionBadge(condition: listing.condition),
                const SizedBox(width: 8),
                TradeValueBadge(value: listing.tradeValueCredits, showLabel: false),
              ],
            ),
            trailing: const Icon(Icons.chevron_right),
          ),
        );
      },
    );
  }
}
