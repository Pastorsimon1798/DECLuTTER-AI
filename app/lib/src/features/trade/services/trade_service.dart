import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/trade_models.dart';

class TradeService {
  final String baseUrl;
  final String? authToken;

  TradeService({
    required this.baseUrl,
    this.authToken,
  });

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (authToken != null) 'Authorization': 'Bearer $authToken',
      };

  Future<List<TradeListing>> findNearby(
    double lat,
    double lon, {
    double radiusKm = 10.0,
  }) async {
    final uri = Uri.parse(
      '$baseUrl/trade/listings/nearby?latitude=$lat&longitude=$lon&radius_km=$radiusKm',
    );
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to load nearby listings: ${response.statusCode}');
    }
    final list = jsonDecode(response.body) as List<dynamic>;
    return list.map((e) => TradeListing.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<TradeListing> createListing({
    required String itemLabel,
    String description = '',
    String condition = 'good',
    double valuationMedianUsd = 0.0,
    double tradeValueCredits = 0.0,
    double? latitude,
    double? longitude,
    List<String> images = const [],
    List<String> tags = const [],
    List<String> wantsInReturn = const [],
  }) async {
    final uri = Uri.parse('$baseUrl/trade/listings');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'item_label': itemLabel,
        'description': description,
        'condition': condition,
        'valuation_median_usd': valuationMedianUsd,
        'trade_value_credits': tradeValueCredits,
        'latitude': latitude,
        'longitude': longitude,
        'images': images,
        'tags': tags,
        'wants_in_return': wantsInReturn,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to create listing: ${response.statusCode}');
    }
    return TradeListing.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<TradeMatch> proposeTrade({
    required String listingId,
    String? offeredListingId,
    String message = '',
    bool useCredits = false,
    double creditAmount = 0.0,
  }) async {
    final uri = Uri.parse('$baseUrl/trade/matches');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'listing_id': listingId,
        'offered_listing_id': offeredListingId,
        'message': message,
        'use_credits': useCredits,
        'credit_amount': creditAmount,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to propose trade: ${response.statusCode}');
    }
    return TradeMatch.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<TradeMatch> acceptTrade(String matchId) async {
    final uri = Uri.parse('$baseUrl/trade/matches/$matchId/accept');
    final response = await http.post(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to accept trade: ${response.statusCode}');
    }
    return TradeMatch.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<TradeMatch> declineTrade(String matchId) async {
    final uri = Uri.parse('$baseUrl/trade/matches/$matchId/decline');
    final response = await http.post(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to decline trade: ${response.statusCode}');
    }
    return TradeMatch.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<CreditBalance> getCreditBalance() async {
    final uri = Uri.parse('$baseUrl/trade/credits');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to load credits: ${response.statusCode}');
    }
    return CreditBalance.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> getConditionChecklist(String condition) async {
    final uri = Uri.parse('$baseUrl/trade/conditions/$condition');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to load checklist: ${response.statusCode}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getTemplates(String intent) async {
    final uri = Uri.parse('$baseUrl/trade/templates/$intent');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to load templates: ${response.statusCode}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getTradeRules() async {
    final uri = Uri.parse('$baseUrl/trade/rules');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to load rules: ${response.statusCode}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<ReputationProfile> getReputation(String userId) async {
    final uri = Uri.parse('$baseUrl/trade/reputation/$userId');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode != 200) {
      throw Exception('Failed to load reputation: ${response.statusCode}');
    }
    return ReputationProfile.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }
}
