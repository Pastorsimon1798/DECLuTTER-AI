import 'package:flutter/material.dart';

import '../services/settings_service.dart';

/// Runtime settings for connecting to a self-hosted DECLuTTER backend.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final SettingsService _settings = SettingsService();
  final _baseUrlController = TextEditingController();
  final _idTokenController = TextEditingController();
  final _appCheckController = TextEditingController();
  bool _useServer = false;
  bool _isLoading = true;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final baseUrl = await _settings.baseUrl ?? '';
    final idToken = await _settings.idToken ?? '';
    final appCheck = await _settings.appCheckToken ?? '';
    final useServer = await _settings.useServer;
    if (mounted) {
      setState(() {
        _baseUrlController.text = baseUrl;
        _idTokenController.text = idToken;
        _appCheckController.text = appCheck;
        _useServer = useServer;
        _isLoading = false;
      });
    }
  }

  Future<void> _save() async {
    await _settings.setBaseUrl(_baseUrlController.text.trim());
    await _settings.setIdToken(_idTokenController.text.trim());
    await _settings.setAppCheckToken(_appCheckController.text.trim());
    await _settings.setUseServer(_useServer);
    if (mounted) {
      setState(() {
        _saved = true;
      });
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          setState(() {
            _saved = false;
          });
        }
      });
    }
  }

  Future<void> _clear() async {
    await _settings.clear();
    if (mounted) {
      setState(() {
        _baseUrlController.clear();
        _idTokenController.clear();
        _appCheckController.clear();
        _useServer = false;
      });
    }
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _idTokenController.dispose();
    _appCheckController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Text(
                    'Self-hosted server',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Connect to your own backend for AI-powered analysis, valuations, and listing pages. Leave blank to use on-device mode only.',
                  ),
                  const SizedBox(height: 16),
                  SwitchListTile(
                    title: const Text('Use backend server'),
                    subtitle: const Text('Enable to sync sessions and valuations remotely'),
                    value: _useServer,
                    onChanged: (value) {
                      setState(() {
                        _useServer = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _baseUrlController,
                    decoration: const InputDecoration(
                      labelText: 'Server URL',
                      hintText: 'https://declutter.example.com',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.url,
                    enabled: _useServer,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _idTokenController,
                    decoration: const InputDecoration(
                      labelText: 'Firebase ID Token',
                      hintText: 'Optional — only if your server requires Firebase auth',
                      border: OutlineInputBorder(),
                    ),
                    enabled: _useServer,
                    obscureText: true,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _appCheckController,
                    decoration: const InputDecoration(
                      labelText: 'App Check Token',
                      hintText: 'Optional — only if your server requires App Check',
                      border: OutlineInputBorder(),
                    ),
                    enabled: _useServer,
                    obscureText: true,
                  ),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: _save,
                          icon: const Icon(Icons.save),
                          label: Text(_saved ? 'Saved!' : 'Save settings'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      OutlinedButton.icon(
                        onPressed: _clear,
                        icon: const Icon(Icons.clear_all),
                        label: const Text('Clear'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Card(
                    elevation: 0,
                    color: theme.colorScheme.surfaceContainerHighest,
                    child: const Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Privacy note',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                          SizedBox(height: 8),
                          Text(
                            'Your server URL and tokens are stored only on this device. No data leaves your device unless you configure a server and enable it above.',
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
