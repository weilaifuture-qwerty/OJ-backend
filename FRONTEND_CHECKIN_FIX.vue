<!-- Update your DailyCheckIn.vue computed property -->

<script>
export default {
  computed: {
    checkedInToday() {
      if (!this.streakData.check_in_days || this.streakData.check_in_days.length === 0) {
        return false;
      }
      
      // Get today's date in local timezone
      const todayLocal = moment().format('YYYY-MM-DD');
      
      // Also get tomorrow's date (in case backend stored UTC date)
      const tomorrowLocal = moment().add(1, 'day').format('YYYY-MM-DD');
      
      // Check if either today or tomorrow is in the check_in_days
      // This handles the case where backend stores UTC date which might be tomorrow
      const checkedToday = this.streakData.check_in_days.includes(todayLocal);
      const checkedTomorrow = this.streakData.check_in_days.includes(tomorrowLocal);
      
      console.log('[DEBUG] checkedInToday:', {
        todayLocal,
        tomorrowLocal,
        check_in_days: this.streakData.check_in_days,
        checkedToday,
        checkedTomorrow,
        result: checkedToday || checkedTomorrow
      });
      
      return checkedToday || checkedTomorrow;
    }
  },
  
  methods: {
    // Update the calendar day checking
    isCheckedIn(day) {
      if (!this.streakData.check_in_days) return false;
      
      const dayStr = moment(day).format('YYYY-MM-DD');
      
      // For calendar display, just check the exact date
      return this.streakData.check_in_days.includes(dayStr);
    },
    
    // Update the handleCheckIn method to send timezone
    async handleCheckIn() {
      console.log('[DEBUG] Check-in clicked at:', {
        'JavaScript Date': new Date().toString(),
        'ISO String': new Date().toISOString(),
        'Local Date String': new Date().toLocaleDateString(),
        'Local Time String': new Date().toLocaleTimeString(),
        'Timezone Offset': new Date().getTimezoneOffset(),
        'Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone
      });
      
      this.checkInLoading = true;
      try {
        // Make sure to send timezone offset
        const response = await api.dailyCheckIn({
          timezone_offset: new Date().getTimezoneOffset()
        });
        
        console.log('[DEBUG] Check-in API response:', response);
        
        if (response.data.error === null) {
          this.streakData = response.data.data;
          console.log('[DEBUG] Streak data received:', this.streakData);
          
          this.$Message.success({
            content: this.$i18n.t('m.Daily_Check_In_Success'),
            duration: 3
          });
          
          // Update calendar
          await this.updateStreak();
        } else {
          this.$Message.error({
            content: response.data.data || this.$i18n.t('m.Check_In_Failed'),
            duration: 5
          });
        }
      } catch (error) {
        console.error('[DEBUG] Check-in error:', error);
        this.$Message.error({
          content: this.$i18n.t('m.Check_In_Failed'),
          duration: 5
        });
      } finally {
        this.checkInLoading = false;
      }
    }
  }
}
</script>

<!-- Also update your API call in api.js -->
<script>
// In api.js
export default {
  // ... other methods ...
  
  dailyCheckIn(data = {}) {
    // Ensure timezone offset is included
    const requestData = {
      timezone_offset: new Date().getTimezoneOffset(),
      ...data
    };
    
    console.log('[API DEBUG] dailyCheckIn request data:', requestData);
    
    return request({
      url: 'daily_check_in',
      method: 'post',
      data: requestData
    });
  }
}
</script>