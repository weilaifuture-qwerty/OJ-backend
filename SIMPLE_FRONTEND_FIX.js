// Simple fix for DailyCheckIn.vue - handles timezone differences

// Replace your checkedInToday computed property with this:
checkedInToday() {
  if (!this.streakData.check_in_days || this.streakData.check_in_days.length === 0) {
    return false;
  }
  
  // Get today's date in local timezone
  const todayLocal = moment().format('YYYY-MM-DD');
  
  // Get yesterday and tomorrow to handle timezone boundaries
  const yesterdayLocal = moment().subtract(1, 'day').format('YYYY-MM-DD');
  const tomorrowLocal = moment().add(1, 'day').format('YYYY-MM-DD');
  
  // Check if any of these dates are in the check_in_days
  const hasToday = this.streakData.check_in_days.includes(todayLocal);
  const hasYesterday = this.streakData.check_in_days.includes(yesterdayLocal);
  const hasTomorrow = this.streakData.check_in_days.includes(tomorrowLocal);
  
  // If we have tomorrow's date, it means we checked in today but backend stored UTC date
  // If we have yesterday's date, check if it was within the last 24 hours
  let checkedInToday = hasToday || hasTomorrow;
  
  // Additional check: if last_check_in was within 24 hours, consider it today
  if (this.streakData.last_check_in) {
    const lastCheckIn = moment(this.streakData.last_check_in);
    const hoursSinceCheckIn = moment().diff(lastCheckIn, 'hours');
    
    if (hoursSinceCheckIn < 24) {
      checkedInToday = true;
    }
  }
  
  console.log('[DEBUG] checkedInToday:', {
    todayLocal,
    yesterdayLocal,
    tomorrowLocal,
    check_in_days: this.streakData.check_in_days,
    hasToday,
    hasYesterday,
    hasTomorrow,
    last_check_in: this.streakData.last_check_in,
    result: checkedInToday
  });
  
  return checkedInToday;
}

// For the calendar, adjust the display to handle timezone differences:
methods: {
  isCheckedIn(day) {
    if (!this.streakData.check_in_days) return false;
    
    const dayStr = moment(day).format('YYYY-MM-DD');
    const dayBefore = moment(day).subtract(1, 'day').format('YYYY-MM-DD');
    const dayAfter = moment(day).add(1, 'day').format('YYYY-MM-DD');
    
    // Check the day itself and adjacent days (for timezone issues)
    return this.streakData.check_in_days.includes(dayStr) ||
           this.streakData.check_in_days.includes(dayBefore) ||
           this.streakData.check_in_days.includes(dayAfter);
  },
  
  // Helper method to get the actual check-in date for display
  getActualCheckInDate(storedDate) {
    // If the stored date is "tomorrow" from user's perspective, 
    // return "today" for display
    const stored = moment(storedDate);
    const today = moment().startOf('day');
    const tomorrow = moment().add(1, 'day').startOf('day');
    
    if (stored.isSame(tomorrow, 'day')) {
      return today.format('YYYY-MM-DD');
    }
    
    return storedDate;
  }
}

// Alternative simpler fix - just check last_check_in time:
checkedInTodaySimple() {
  if (!this.streakData.last_check_in) {
    return false;
  }
  
  // Check if last check-in was less than 24 hours ago
  const lastCheckIn = moment(this.streakData.last_check_in);
  const now = moment();
  const hoursDiff = now.diff(lastCheckIn, 'hours');
  
  return hoursDiff < 24;
}