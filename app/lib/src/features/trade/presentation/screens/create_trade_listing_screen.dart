import 'package:flutter/material.dart';

import '../../services/trade_service.dart';

class CreateTradeListingScreen extends StatefulWidget {
  final double? tradeValueCredits;
  final String? itemLabel;

  const CreateTradeListingScreen({
    super.key,
    this.tradeValueCredits,
    this.itemLabel,
  });

  @override
  State<CreateTradeListingScreen> createState() => _CreateTradeListingScreenState();
}

class _CreateTradeListingScreenState extends State<CreateTradeListingScreen> {
  final _formKey = GlobalKey<FormState>();
  final _service = TradeService(baseUrl: 'https://kyanitelabs.tech/declutter');

  final _labelController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _valueController = TextEditingController();
  final _wantsController = TextEditingController();

  String _condition = 'good';
  bool _noNegotiation = false;
  bool _loading = false;
  int _currentStep = 0;

  static const _conditions = ['new', 'like_new', 'good', 'fair', 'for_parts'];

  @override
  void initState() {
    super.initState();
    if (widget.itemLabel != null) {
      _labelController.text = widget.itemLabel!;
    }
    if (widget.tradeValueCredits != null) {
      _valueController.text = widget.tradeValueCredits!.toStringAsFixed(0);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await _service.createListing(
        itemLabel: _labelController.text.trim(),
        description: _descriptionController.text.trim(),
        condition: _condition,
        tradeValueCredits: double.tryParse(_valueController.text) ?? 0.0,
        tags: _noNegotiation ? ['no_negotiation'] : [],
        wantsInReturn: _wantsController.text
            .split(',')
            .map((s) => s.trim())
            .where((s) => s.isNotEmpty)
            .toList(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Trade listing created!')),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Trade Listing')),
      body: Form(
        key: _formKey,
        child: Stepper(
          currentStep: _currentStep,
          onStepContinue: () {
            if (_currentStep < 3) {
              setState(() => _currentStep++);
            } else {
              _submit();
            }
          },
          onStepCancel: () {
            if (_currentStep > 0) {
              setState(() => _currentStep--);
            }
          },
          controlsBuilder: (context, details) {
            return Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Row(
                children: [
                  FilledButton(
                    onPressed: _loading ? null : details.onStepContinue,
                    child: _loading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(_currentStep == 3 ? 'Create Listing' : 'Next'),
                  ),
                  const SizedBox(width: 12),
                  if (_currentStep > 0)
                    TextButton(
                      onPressed: details.onStepCancel,
                      child: const Text('Back'),
                    ),
                ],
              ),
            );
          },
          steps: [
            Step(
              title: const Text('Item Info'),
              isActive: _currentStep >= 0,
              content: Column(
                children: [
                  TextFormField(
                    controller: _labelController,
                    decoration: const InputDecoration(
                      labelText: 'Item name *',
                      border: OutlineInputBorder(),
                    ),
                    validator: (v) => v == null || v.isEmpty ? 'Required' : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _descriptionController,
                    decoration: const InputDecoration(
                      labelText: 'Description',
                      border: OutlineInputBorder(),
                      hintText: 'Size, color, brand, etc.',
                    ),
                    maxLines: 3,
                  ),
                ],
              ),
            ),
            Step(
              title: const Text('Condition'),
              isActive: _currentStep >= 1,
              content: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Select condition:', style: TextStyle(fontSize: 14)),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _conditions.map((c) => ChoiceChip(
                      label: Text(c.toUpperCase()),
                      selected: _condition == c,
                      onSelected: (selected) {
                        if (selected) setState(() => _condition = c);
                      },
                    )).toList(),
                  ),
                  const SizedBox(height: 16),
                  if (_condition.isNotEmpty)
                    FutureBuilder(
                      future: _service.getConditionChecklist(_condition),
                      builder: (context, snapshot) {
                        if (!snapshot.hasData) return const SizedBox.shrink();
                        final items = (snapshot.data!['checklist'] as List<dynamic>).cast<String>();
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Checklist:',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 8),
                            ...items.map((item) => Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Row(
                                children: [
                                  const Icon(Icons.check_circle_outline, size: 18, color: Colors.green),
                                  const SizedBox(width: 8),
                                  Expanded(child: Text(item, style: const TextStyle(fontSize: 13))),
                                ],
                              ),
                            )),
                          ],
                        );
                      },
                    ),
                ],
              ),
            ),
            Step(
              title: const Text('Trade Value'),
              isActive: _currentStep >= 2,
              content: Column(
                children: [
                  TextFormField(
                    controller: _valueController,
                    decoration: const InputDecoration(
                      labelText: 'Trade value in credits *',
                      border: OutlineInputBorder(),
                      helperText: '1 credit = \$1 fair trade value',
                      suffixText: 'credits',
                    ),
                    keyboardType: TextInputType.number,
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Required';
                      final n = double.tryParse(v);
                      if (n == null || n < 0) return 'Must be a positive number';
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _wantsController,
                    decoration: const InputDecoration(
                      labelText: 'Wants in return (comma-separated)',
                      border: OutlineInputBorder(),
                      hintText: 'e.g. brushes, canvas, pencils',
                    ),
                  ),
                ],
              ),
            ),
            Step(
              title: const Text('Preferences'),
              isActive: _currentStep >= 3,
              content: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SwitchListTile(
                    title: const Text('No negotiation'),
                    subtitle: const Text('Trade value is fixed'),
                    value: _noNegotiation,
                    onChanged: (v) => setState(() => _noNegotiation = v),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
