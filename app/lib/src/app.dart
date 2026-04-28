import 'package:flutter/material.dart';

import 'features/capture/presentation/capture_screen.dart';
import 'features/trade/presentation/screens/trade_hub_screen.dart';

class DeclutterAIApp extends StatelessWidget {
  const DeclutterAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DECLuTTER AI',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF5D63FF)),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const DeclutterHomeScreen(),
    );
  }
}

class DeclutterHomeScreen extends StatefulWidget {
  const DeclutterHomeScreen({super.key});

  @override
  State<DeclutterHomeScreen> createState() => _DeclutterHomeScreenState();
}

class _DeclutterHomeScreenState extends State<DeclutterHomeScreen> {
  int _currentIndex = 0;

  final _screens = const [
    CaptureScreen(),
    TradeHubScreen(),
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
            icon: Icon(Icons.camera_alt_outlined),
            selectedIcon: Icon(Icons.camera_alt),
            label: 'Declutter',
          ),
          NavigationDestination(
            icon: Icon(Icons.swap_horiz_outlined),
            selectedIcon: Icon(Icons.swap_horiz),
            label: 'Trade',
          ),
        ],
      ),
    );
  }
}
