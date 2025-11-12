/**
 * Unit conversion utilities
 * Converts between metric (meters, kilometers) and imperial (feet, miles)
 */

/**
 * Convert meters to feet
 */
export const metersToFeet = (meters) => {
  return meters * 3.28084;
};

/**
 * Convert meters to miles
 */
export const metersToMiles = (meters) => {
  return meters * 0.000621371;
};

/**
 * Convert feet to meters
 */
export const feetToMeters = (feet) => {
  return feet * 0.3048;
};

/**
 * Convert miles to meters
 */
export const milesToMeters = (miles) => {
  return miles * 1609.34;
};

/**
 * Format distance in meters to a human-readable string
 * @param {number} meters - Distance in meters
 * @param {string} unitSystem - 'metric' or 'imperial'
 * @returns {string} Formatted distance string
 */
export const formatDistance = (meters, unitSystem = 'metric') => {
  if (!meters && meters !== 0) return null;

  if (unitSystem === 'imperial') {
    const miles = metersToMiles(meters);
    if (miles < 0.1) {
      const feet = Math.round(metersToFeet(meters));
      return `${feet} ft`;
    } else if (miles < 10) {
      return `${miles.toFixed(1)} mi`;
    } else {
      return `${Math.round(miles)} mi`;
    }
  } else {
    // Metric (default)
    if (meters < 1000) {
      return `${Math.round(meters)} m`;
    } else if (meters < 10000) {
      return `${(meters / 1000).toFixed(1)} km`;
    } else {
      return `${Math.round(meters / 1000)} km`;
    }
  }
};

/**
 * Format distance for display with "away" suffix
 * @param {number} meters - Distance in meters
 * @param {string} unitSystem - 'metric' or 'imperial'
 * @returns {string} Formatted distance string with "away"
 */
export const formatDistanceAway = (meters, unitSystem = 'metric') => {
  if (!meters && meters !== 0) return 'Location hidden for privacy';
  
  const distance = formatDistance(meters, unitSystem);
  return `${distance} away`;
};

/**
 * Convert radius from display units to meters for API calls
 * @param {number} value - Radius value in display units
 * @param {string} unitSystem - 'metric' or 'imperial'
 * @returns {number} Radius in meters
 */
export const radiusToMeters = (value, unitSystem = 'metric') => {
  if (unitSystem === 'imperial') {
    return milesToMeters(value);
  }
  return value; // Already in meters for metric
};

/**
 * Convert radius from meters to display units
 * @param {number} meters - Radius in meters
 * @param {string} unitSystem - 'metric' or 'imperial'
 * @returns {number} Radius in display units
 */
export const radiusFromMeters = (meters, unitSystem = 'metric') => {
  if (unitSystem === 'imperial') {
    return metersToMiles(meters);
  }
  return meters / 1000; // Convert to kilometers for display
};

/**
 * Get radius slider min/max values in display units
 * @param {string} unitSystem - 'metric' or 'imperial'
 * @returns {object} { min, max, step }
 */
export const getRadiusSliderConfig = (unitSystem = 'metric') => {
  if (unitSystem === 'imperial') {
    // 0.1 miles to 500 miles
    return {
      min: 0.1,
      max: 500,
      step: 0.1,
      minMeters: 500,
      maxMeters: 804672, // 500 miles in meters
    };
  } else {
    // 0.5 km to 800 km (approximately 500 miles)
    return {
      min: 0.5,
      max: 800,
      step: 0.5,
      minMeters: 500,
      maxMeters: 804672, // 500 miles in meters
    };
  }
};

