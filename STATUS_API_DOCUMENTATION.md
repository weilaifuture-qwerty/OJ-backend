# Status System API Documentation

## Overview

The status system allows users to set their current activity status, mood message, emoji, and status color. It supports auto-expiration of mood messages and integrates with various platform activities.

## API Endpoints

### 1. Get User Status
**GET** `/api/user_status/`

Get the current user's status information.

**Response:**
```json
{
  "error": null,
  "data": {
    "status": "practicing",
    "status_message": "Working on dynamic programming problems",
    "mood_emoji": "💡",
    "mood_clear_at": "2024-01-20T15:30:00Z",
    "status_color": "#52c41a"
  }
}
```

### 2. Update User Status
**PUT** `/api/user_status/`

Update the current user's status.

**Request Body:**
```json
{
  "status": "learning",
  "status_message": "Studying graph algorithms",
  "mood_emoji": "📚",
  "mood_clear_at": "2024-01-20T18:00:00Z",
  "status_color": "#1890ff"
}
```

**Response:**
```json
{
  "error": null,
  "data": {
    "status": "learning",
    "status_message": "Studying graph algorithms",
    "mood_emoji": "📚",
    "mood_clear_at": "2024-01-20T18:00:00Z",
    "status_color": "#1890ff"
  }
}
```

### 3. Update Profile (includes status)
**PUT** `/api/profile/`

The existing profile update endpoint also accepts status fields.

**Request Body:**
```json
{
  "real_name": "John Doe",
  "status": "debugging",
  "status_message": "Fixing that tricky bug",
  "mood_emoji": "🐛",
  "status_color": "#fa8c16"
}
```

## Status Options

| Status | Display Name | Default Color | Description |
|--------|-------------|---------------|-------------|
| `practicing` | Practicing | #52c41a | Default status, solving problems |
| `learning` | Learning | #1890ff | Studying new concepts |
| `competing` | In Contest | #f5222d | Participating in a contest |
| `debugging` | Debugging | #fa8c16 | Fixing code issues |
| `reviewing` | Reviewing | #722ed1 | Reviewing solutions |
| `resting` | Taking Break | #8c8c8c | Away from coding |

## Field Specifications

### status
- **Type:** String
- **Required:** No
- **Default:** "practicing"
- **Choices:** practicing, learning, competing, debugging, reviewing, resting

### status_message
- **Type:** String
- **Required:** No
- **Max Length:** 100 characters
- **Default:** null
- **Description:** Custom message describing current activity

### mood_emoji
- **Type:** String
- **Required:** No
- **Max Length:** 10 characters
- **Default:** null
- **Description:** Emoji to display with status

### mood_clear_at
- **Type:** DateTime (ISO 8601)
- **Required:** No
- **Default:** null
- **Description:** When to automatically clear mood message and emoji

### status_color
- **Type:** String (Hex color)
- **Required:** No
- **Default:** "#52c41a"
- **Format:** #RRGGBB (6-digit hex color)
- **Validation:** Must match regex `^#[0-9A-Fa-f]{6}$`

## Examples

### Set Learning Status
```javascript
const response = await fetch('/api/user_status/', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  },
  body: JSON.stringify({
    status: 'learning',
    status_message: 'Studying dynamic programming',
    mood_emoji: '📖',
    status_color: '#1890ff',
    mood_clear_at: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString() // 4 hours
  })
});
```

### Set Contest Status
```javascript
const response = await fetch('/api/user_status/', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  },
  body: JSON.stringify({
    status: 'competing',
    status_message: 'Codeforces Round #842',
    mood_emoji: '🏆',
    status_color: '#f5222d'
  })
});
```

### Clear Status Message
```javascript
const response = await fetch('/api/user_status/', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken()
  },
  body: JSON.stringify({
    status_message: '',
    mood_emoji: '',
    mood_clear_at: null
  })
});
```

## Auto-Clear Feature

The `mood_clear_at` field enables automatic clearing of mood messages:

1. Set `mood_clear_at` to a future timestamp
2. Run the management command periodically: `python manage.py clear_expired_moods`
3. Or set up a cron job: `*/5 * * * * python manage.py clear_expired_moods`

When cleared:
- `status_message` is set to empty string
- `mood_emoji` is set to empty string
- `mood_clear_at` is set to null
- `status` and `status_color` remain unchanged

## Error Responses

### Invalid Status Choice
```json
{
  "error": "invalid-status",
  "data": "status: Select a valid choice. invalid is not one of the available choices."
}
```

### Invalid Color Format
```json
{
  "error": "invalid-status_color",
  "data": "status_color: Invalid color format. Use hex format like #52c41a"
}
```

### Status Message Too Long
```json
{
  "error": "invalid-status_message",
  "data": "status_message: Ensure this field has no more than 100 characters."
}
```

## Integration Points

### Contest System
When a user joins a contest, automatically update their status:
```python
profile.status = 'competing'
profile.status_message = f'Competing in {contest.title}'
profile.mood_emoji = '🏆'
profile.status_color = '#f5222d'
profile.mood_clear_at = contest.end_time
```

### Problem Submission
Update status based on submission results:
```python
if result == 'Accepted':
    profile.status = 'practicing'
    profile.mood_emoji = '✅'
elif result == 'Wrong Answer':
    profile.status = 'debugging'
    profile.mood_emoji = '🔧'
```

### Learning Materials
When accessing tutorials or documentation:
```python
profile.status = 'learning'
profile.status_message = f'Learning about {topic}'
profile.mood_emoji = '📚'
```