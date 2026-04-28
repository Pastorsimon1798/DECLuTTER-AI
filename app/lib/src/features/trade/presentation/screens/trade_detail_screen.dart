import 'package:flutter/material.dart';

import '../../models/trade_models.dart';
import '../../services/trade_service.dart';
import '../widgets/condition_badge.dart';
import '../widgets/template_picker.dart';
import '../widgets/trade_value_badge.dart';

class TradeDetailScreen extends StatefulWidget {
  final TradeListing listing;

  const TradeDetailScreen({super.key, required this.listing});

  @override
  State<TradeDetailScreen> createState() => _TradeDetailScreenState();
}

class _TradeDetailScreenState extends State<TradeDetailScreen> {
  final TradeService _service = TradeService(
    baseUrl: 'https://kyanitelabs.tech/declutter',
  );

  List<String> _checklist = [];
  List<String> _templates = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    try {
      final checklistData = await _service.getConditionChecklist(widget.listing.condition);
      final templatesData = await _service.getTemplates('propose');
      setState(() {
        _checklist = (checklistData['checklist'] as List<dynamic>).cast<String>();
        _templates = (templatesData['templates'] as List<dynamic>).cast<String>();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  void _showProposeDialog() {
    String selectedMessage = '';
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
          left: 16,
          right: 16,
          top: 16,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Propose Trade',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            TemplatePicker(
              templates: _templates,
              onSelected: (msg) {
                selectedMessage = msg;
                Navigator.pop(context);
                _proposeTrade(selectedMessage);
              },
            ),
            const SizedBox(height: 16),
            TextField(
              decoration: const InputDecoration(
                labelText: 'Or write your own message',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
              onChanged: (v) => selectedMessage = v,
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  Navigator.pop(context);
                  _proposeTrade(selectedMessage);
                },
                child: const Text('Send Proposal'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Future<void> _proposeTrade(String message) async {
    try {
      await _service.proposeTrade(
        listingId: widget.listing.id,
        message: message,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Trade proposal sent!')),
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
    final listing = widget.listing;
    return Scaffold(
      appBar: AppBar(title: Text(listing.itemLabel)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                ConditionBadge(condition: listing.condition, large: true),
                const SizedBox(width: 12),
                TradeValueBadge(value: listing.tradeValueCredits),
              ],
            ),
            const SizedBox(height: 16),
            if (listing.description.isNotEmpty) ...[
              const Text(
                'Description',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(listing.description, style: const TextStyle(fontSize: 15)),
              const SizedBox(height: 16),
            ],
            const Text(
              'Condition Checklist',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else
              ..._checklist.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.check_circle_outline, size: 20, color: Colors.green),
                        const SizedBox(width: 8),
                        Expanded(child: Text(item, style: const TextStyle(fontSize: 14))),
                      ],
                    ),
                  )),
            const SizedBox(height: 16),
            if (listing.tags.isNotEmpty) ...[
              const Text(
                'Tags',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: listing.tags.map((t) => Chip(label: Text(t))).toList(),
              ),
              const SizedBox(height: 16),
            ],
            if (listing.wantsInReturn.isNotEmpty) ...[
              const Text(
                'Wants in Return',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: listing.wantsInReturn.map((w) => Chip(
                  label: Text(w),
                  backgroundColor: Colors.amber.shade100,
                )).toList(),
              ),
              const SizedBox(height: 16),
            ],
            const SizedBox(height: 80),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showProposeDialog,
        icon: const Icon(Icons.swap_horiz),
        label: const Text('Propose Trade'),
      ),
    );
  }
}
