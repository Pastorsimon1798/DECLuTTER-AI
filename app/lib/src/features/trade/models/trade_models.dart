class TradeListing {
  final String id;
  final String userId;
  final String itemLabel;
  final String description;
  final String condition;
  final double valuationMedianUsd;
  final double tradeValueCredits;
  final double? latitude;
  final double? longitude;
  final List<String> images;
  final List<String> tags;
  final List<String> wantsInReturn;
  final String status;
  final String createdAt;
  final double? distanceKm;

  TradeListing({
    required this.id,
    required this.userId,
    required this.itemLabel,
    this.description = '',
    this.condition = 'good',
    this.valuationMedianUsd = 0.0,
    this.tradeValueCredits = 0.0,
    this.latitude,
    this.longitude,
    this.images = const [],
    this.tags = const [],
    this.wantsInReturn = const [],
    this.status = 'available',
    required this.createdAt,
    this.distanceKm,
  });

  factory TradeListing.fromJson(Map<String, dynamic> json) => TradeListing(
        id: json['id'] as String,
        userId: json['user_id'] as String,
        itemLabel: json['item_label'] as String,
        description: json['description'] as String? ?? '',
        condition: json['condition'] as String? ?? 'good',
        valuationMedianUsd: (json['valuation_median_usd'] as num?)?.toDouble() ?? 0.0,
        tradeValueCredits: (json['trade_value_credits'] as num?)?.toDouble() ?? 0.0,
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
        images: (json['images'] as List<dynamic>?)?.cast<String>() ?? const [],
        tags: (json['tags'] as List<dynamic>?)?.cast<String>() ?? const [],
        wantsInReturn: (json['wants_in_return'] as List<dynamic>?)?.cast<String>() ?? const [],
        status: json['status'] as String? ?? 'available',
        createdAt: json['created_at'] as String,
        distanceKm: (json['distance_km'] as num?)?.toDouble(),
      );
}

class TradeMatch {
  final String id;
  final String listingId;
  final String requesterId;
  final String ownerId;
  final String? offeredListingId;
  final String message;
  final bool useCredits;
  final double creditAmount;
  final String status;
  final String createdAt;

  TradeMatch({
    required this.id,
    required this.listingId,
    required this.requesterId,
    required this.ownerId,
    this.offeredListingId,
    this.message = '',
    this.useCredits = false,
    this.creditAmount = 0.0,
    this.status = 'pending',
    required this.createdAt,
  });

  factory TradeMatch.fromJson(Map<String, dynamic> json) => TradeMatch(
        id: json['id'] as String,
        listingId: json['listing_id'] as String,
        requesterId: json['requester_id'] as String,
        ownerId: json['owner_id'] as String,
        offeredListingId: json['offered_listing_id'] as String?,
        message: json['message'] as String? ?? '',
        useCredits: json['use_credits'] as bool? ?? false,
        creditAmount: (json['credit_amount'] as num?)?.toDouble() ?? 0.0,
        status: json['status'] as String? ?? 'pending',
        createdAt: json['created_at'] as String,
      );
}

class CreditTransaction {
  final double amount;
  final String itemLabel;
  final String direction;
  final String createdAt;

  CreditTransaction({
    required this.amount,
    required this.itemLabel,
    required this.direction,
    required this.createdAt,
  });

  factory CreditTransaction.fromJson(Map<String, dynamic> json) => CreditTransaction(
        amount: (json['amount'] as num).toDouble(),
        itemLabel: json['item_label'] as String,
        direction: json['direction'] as String,
        createdAt: json['created_at'] as String,
      );
}

class CreditBalance {
  final double balance;
  final List<CreditTransaction> transactions;

  CreditBalance({
    required this.balance,
    required this.transactions,
  });

  factory CreditBalance.fromJson(Map<String, dynamic> json) => CreditBalance(
        balance: (json['balance'] as num).toDouble(),
        transactions: (json['transactions'] as List<dynamic>)
            .map((e) => CreditTransaction.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class ReputationProfile {
  final String userId;
  final double averageRating;
  final int totalTrades;
  final List<String> topTags;

  ReputationProfile({
    required this.userId,
    required this.averageRating,
    required this.totalTrades,
    required this.topTags,
  });

  factory ReputationProfile.fromJson(Map<String, dynamic> json) => ReputationProfile(
        userId: json['user_id'] as String,
        averageRating: (json['average_rating'] as num).toDouble(),
        totalTrades: json['total_trades'] as int,
        topTags: (json['top_tags'] as List<dynamic>).cast<String>(),
      );
}
