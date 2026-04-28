import 'package:flutter/material.dart';

import '../../models/trade_models.dart';
import '../../services/trade_service.dart';
import '../widgets/condition_badge.dart';
import '../widgets/trade_value_badge.dart';
import 'trade_detail_screen.dart';

class BrowseTradesScreen extends StatefulWidget {
  const BrowseTradesScreen({super.key});

  @override
  State<BrowseTradesScreen> createState() => _BrowseTradesScreenState();
}

class _BrowseTradesScreenState extends State<BrowseTradesScreen> {
  final TradeService _service = TradeService(
    baseUrl: 'https://kyanitelabs.tech/declutter',
  );

  List<TradeListing> _listings = [];
  bool _loading = true;
  String? _error;
  double _radiusKm = 10.0;

  @override
  void initState() {
    super.initState();
    _loadListings();
  }

  Future<void> _loadListings() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // Default to a sample location (Toronto area)
      final listings = await _service.findNearby(43.65, -79.38, radiusKm: _radiusKm);
      setState(() {
        _listings = listings;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Browse Trades'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadListings,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.location_on, color: Color(0xFF5D63FF)),
                const SizedBox(width: 8),
                Text('Within ${_radiusKm.toStringAsFixed(0)} km'),
                const Spacer(),
                SegmentedButton<double>(
                  segments: const [
                    ButtonSegment(value: 5.0, label: Text('5 km')),
                    ButtonSegment(value: 10.0, label: Text('10 km')),
                    ButtonSegment(value: 25.0, label: Text('25 km')),
                  ],
                  selected: {_radiusKm},
                  onSelectionChanged: (set) {
                    setState(() => _radiusKm = set.first);
                    _loadListings();
                  },
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(child: Text('Error: $_error'))
                    : _listings.isEmpty
                        ? const Center(child: Text('No trade listings nearby'))
                        : ListView.builder(
                            itemCount: _listings.length,
                            itemBuilder: (context, index) {
                              final listing = _listings[index];
                              return _ListingCard(
                                listing: listing,
                                onTap: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => TradeDetailScreen(listing: listing),
                                  ),
                                ),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}

class _ListingCard extends StatelessWidget {
  final TradeListing listing;
  final VoidCallback onTap;

  const _ListingCard({required this.listing, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      listing.itemLabel,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  ConditionBadge(condition: listing.condition),
                ],
              ),
              const SizedBox(height: 8),
              if (listing.description.isNotEmpty)
                Text(
                  listing.description,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey.shade700,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  TradeValueBadge(value: listing.tradeValueCredits),
                  if (listing.distanceKm != null)
                    Chip(
                      avatar: const Icon(Icons.location_on, size: 16),
                      label: Text('${listing.distanceKm!.toStringAsFixed(1)} km'),
                    ),
                  ...listing.tags.map((tag) => Chip(
                        label: Text(tag),
                        visualDensity: VisualDensity.compact,
                      )),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
