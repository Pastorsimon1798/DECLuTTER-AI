/**
 * Hours Parser Utility
 * Phase 3.5: Parse resource hours and determine if currently open
 */

/**
 * Parse hours object and check if resource is currently open
 * @param {Object} hours - Hours object from resource (e.g., {monday: "9:00 AM - 5:00 PM", ...})
 * @returns {boolean} - Whether the resource is currently open
 */
export function isOpenNow(hours) {
  if (!hours || typeof hours !== 'object') return false;

  const now = new Date();
  const currentDay = now.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
  const currentTime = now.getHours() * 60 + now.getMinutes(); // Minutes since midnight

  const todayHours = hours[currentDay];
  if (!todayHours) return false;

  // Handle "Closed" or empty strings
  if (!todayHours || todayHours.toLowerCase() === 'closed') return false;

  // Handle "24 hours" or "Open 24 hours"
  if (todayHours.toLowerCase().includes('24 hour')) return true;

  // Parse time ranges (e.g., "9:00 AM - 5:00 PM")
  const timeRangeMatch = todayHours.match(/(\d{1,2}):?(\d{2})?\s*(AM|PM)?\s*-\s*(\d{1,2}):?(\d{2})?\s*(AM|PM)?/i);

  if (!timeRangeMatch) return false;

  const [_, startHour, startMin = '0', startPeriod, endHour, endMin = '0', endPeriod] = timeRangeMatch;

  // Convert to 24-hour format
  let openTime = parseInt(startHour) * 60 + parseInt(startMin);
  let closeTime = parseInt(endHour) * 60 + parseInt(endMin);

  // Adjust for AM/PM
  if (startPeriod?.toUpperCase() === 'PM' && parseInt(startHour) !== 12) {
    openTime += 12 * 60;
  } else if (startPeriod?.toUpperCase() === 'AM' && parseInt(startHour) === 12) {
    openTime = parseInt(startMin);
  }

  if (endPeriod?.toUpperCase() === 'PM' && parseInt(endHour) !== 12) {
    closeTime += 12 * 60;
  } else if (endPeriod?.toUpperCase() === 'AM' && parseInt(endHour) === 12) {
    closeTime = parseInt(endMin);
  }

  // Handle cases where closing time is past midnight
  if (closeTime < openTime) {
    return currentTime >= openTime || currentTime <= closeTime;
  }

  return currentTime >= openTime && currentTime <= closeTime;
}

/**
 * Format hours object for display
 * @param {Object} hours - Hours object from resource
 * @returns {Array} - Array of formatted day/hours objects
 */
export function formatHours(hours) {
  if (!hours || typeof hours !== 'object') return [];

  const daysOrder = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

  return daysOrder.map(day => ({
    day: day.charAt(0).toUpperCase() + day.slice(1),
    hours: hours[day] || 'Closed',
    isToday: day === new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase()
  })).filter(item => item.hours);
}

/**
 * Get a human-readable status for the resource
 * @param {Object} hours - Hours object from resource
 * @returns {Object} - {isOpen: boolean, status: string, nextChange: string}
 */
export function getOpenStatus(hours) {
  const open = isOpenNow(hours);

  if (!hours) {
    return {
      isOpen: false,
      status: 'Hours not available',
      statusColor: 'gray'
    };
  }

  if (open) {
    return {
      isOpen: true,
      status: 'Open Now',
      statusColor: 'green'
    };
  }

  return {
    isOpen: false,
    status: 'Closed',
    statusColor: 'red'
  };
}

/**
 * Parse a single time range string
 * @param {string} timeRange - e.g., "9:00 AM - 5:00 PM"
 * @returns {string} - Formatted time range
 */
export function parseTimeRange(timeRange) {
  if (!timeRange) return 'Closed';

  // If already formatted nicely, return as-is
  if (timeRange.includes('-') || timeRange.toLowerCase() === 'closed') {
    return timeRange;
  }

  // Handle 24-hour format
  if (timeRange.toLowerCase().includes('24')) {
    return 'Open 24 hours';
  }

  return timeRange;
}
