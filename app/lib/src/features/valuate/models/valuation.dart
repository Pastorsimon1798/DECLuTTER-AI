/// Immutable resale-value estimate for a detection group.
class Valuation {
  const Valuation({
    required this.low,
    required this.mid,
    required this.high,
    required this.confidence,
  });

  final double low;
  final double mid;
  final double high;
  final double confidence;

  factory Valuation.fromJson(Map<String, dynamic> json) {
    return Valuation(
      low: _readDouble(json['low']),
      mid: _readDouble(json['mid']),
      high: _readDouble(json['high']),
      confidence: _readDouble(json['confidence']),
    );
  }

  Map<String, dynamic> toJson() => {
        'low': low,
        'mid': mid,
        'high': high,
        'confidence': confidence,
      };

  @override
  bool operator ==(Object other) =>
      other is Valuation &&
      other.low == low &&
      other.mid == mid &&
      other.high == high &&
      other.confidence == confidence;

  @override
  int get hashCode => Object.hash(low, mid, high, confidence);

  @override
  String toString() =>
      'Valuation(low: \$${low.toStringAsFixed(2)}, mid: \$${mid.toStringAsFixed(2)}, high: \$${high.toStringAsFixed(2)}, confidence: $confidence)';
}

double _readDouble(Object? value) {
  if (value is num) {
    return value.toDouble();
  }
  return 0;
}
