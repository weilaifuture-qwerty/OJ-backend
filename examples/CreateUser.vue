<template>
  <div class="create-user-container">
    <Card class="create-user-card">
      <template #header>
        <div class="card-header">
          <h2><Icon type="md-person-add" /> Create New User</h2>
          <p>Add a new user to the Online Judge system</p>
        </div>
      </template>

      <Alert v-if="successMessage" type="success" show-icon closable @on-close="successMessage = ''">
        {{ successMessage }}
      </Alert>

      <Alert v-if="errorMessage" type="error" show-icon closable @on-close="errorMessage = ''">
        {{ errorMessage }}
      </Alert>

      <Form ref="createUserForm" :model="formData" :rules="formRules" @submit.native.prevent="handleSubmit">
        <FormItem label="Username" prop="username">
          <Input 
            v-model="formData.username" 
            placeholder="Enter username"
            prefix="ios-person-outline"
            size="large"
            @on-change="handleUsernameChange"
          >
            <template #suffix>
              <Icon v-if="usernameValid === true" type="ios-checkmark-circle" color="#19be6b" />
              <Icon v-if="usernameValid === false" type="ios-close-circle" color="#ed4014" />
            </template>
          </Input>
        </FormItem>

        <FormItem label="Password" prop="password">
          <Input 
            v-model="formData.password" 
            type="password" 
            placeholder="Enter password (min 6 characters)"
            prefix="ios-lock-outline"
            size="large"
            @on-change="checkPasswordStrength"
          />
          <div v-if="formData.password" class="password-strength">
            <div class="strength-text">Password strength: {{ passwordStrengthText }}</div>
            <Progress 
              :percent="passwordStrengthPercent" 
              :stroke-color="passwordStrengthColor"
              :show-text="false"
              stroke-width="6"
            />
          </div>
        </FormItem>

        <FormItem label="Real Name" prop="real_name">
          <Input 
            v-model="formData.real_name" 
            placeholder="Enter real name (optional)"
            prefix="ios-contact-outline"
            size="large"
          />
        </FormItem>

        <FormItem label="User Type">
          <RadioGroup v-model="formData.userType" type="button" size="large">
            <Radio label="regular">
              <Icon type="ios-person" /> Regular User
            </Radio>
            <Radio label="admin">
              <Icon type="md-build" /> Admin
            </Radio>
            <Radio label="super">
              <Icon type="md-star" /> Super Admin
            </Radio>
          </RadioGroup>
        </FormItem>

        <FormItem label="Additional Options">
          <Row :gutter="16">
            <Col span="12">
              <Checkbox v-model="formData.openApi" size="large">
                <Icon type="md-key" /> Enable API Access
              </Checkbox>
            </Col>
            <Col span="12">
              <Checkbox v-model="formData.twoFactorAuth" size="large">
                <Icon type="md-phone-portrait" /> Enable 2FA
              </Checkbox>
            </Col>
          </Row>
        </FormItem>

        <FormItem>
          <div class="button-group">
            <Button @click="resetForm" size="large">
              <Icon type="md-refresh" /> Reset
            </Button>
            <Button 
              type="primary" 
              @click="handleSubmit" 
              :loading="loading"
              size="large"
              long
            >
              <Icon type="md-checkmark" /> Create User
            </Button>
          </div>
        </FormItem>
      </Form>

      <Divider />

      <div class="recent-users">
        <h3><Icon type="md-time" /> Recently Created Users</h3>
        <List size="small">
          <ListItem v-for="user in recentUsers" :key="user.username">
            <ListItemMeta 
              :avatar-icon="getUserIcon(user.type)"
              :title="user.username"
              :description="`${user.real_name || 'No name'} - Created ${formatTime(user.created_at)}`"
            />
            <template #action>
              <li>
                <Tag :color="getUserTagColor(user.type)">{{ user.type }}</Tag>
              </li>
            </template>
          </ListItem>
        </List>
      </div>
    </Card>
  </div>
</template>

<script>
import api from '@/utils/api'

export default {
  name: 'CreateUser',
  data() {
    return {
      formData: {
        username: '',
        password: '',
        real_name: '',
        userType: 'regular',
        openApi: false,
        twoFactorAuth: false
      },
      formRules: {
        username: [
          { required: true, message: 'Username is required', trigger: 'blur' },
          { min: 3, max: 32, message: 'Username must be 3-32 characters', trigger: 'blur' },
          { pattern: /^[a-zA-Z0-9_]+$/, message: 'Username can only contain letters, numbers and underscore', trigger: 'blur' }
        ],
        password: [
          { required: true, message: 'Password is required', trigger: 'blur' },
          { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
        ]
      },
      loading: false,
      successMessage: '',
      errorMessage: '',
      usernameValid: null,
      passwordStrength: 0,
      recentUsers: [
        { username: 'testuser', real_name: 'Test User', type: 'Regular', created_at: new Date() },
        { username: 'adminuser', real_name: 'Admin User', type: 'Admin', created_at: new Date() }
      ]
    }
  },
  computed: {
    passwordStrengthPercent() {
      return this.passwordStrength * 20
    },
    passwordStrengthColor() {
      if (this.passwordStrength <= 2) return '#ed4014'
      if (this.passwordStrength <= 3) return '#ff9900'
      return '#19be6b'
    },
    passwordStrengthText() {
      if (this.passwordStrength <= 2) return 'Weak'
      if (this.passwordStrength <= 3) return 'Medium'
      return 'Strong'
    }
  },
  methods: {
    async handleSubmit() {
      const valid = await this.$refs.createUserForm.validate()
      if (!valid) return

      this.loading = true
      this.successMessage = ''
      this.errorMessage = ''

      try {
        // Map user type to admin type
        let adminType = 'Regular User'
        if (this.formData.userType === 'admin') adminType = 'Admin'
        if (this.formData.userType === 'super') adminType = 'Super Admin'

        const response = await api.createUser({
          username: this.formData.username.toLowerCase(),
          password: this.formData.password,
          real_name: this.formData.real_name,
          admin_type: adminType,
          open_api: this.formData.openApi,
          two_factor_auth: this.formData.twoFactorAuth
        })

        this.successMessage = `User "${this.formData.username}" created successfully!`
        
        // Add to recent users
        this.recentUsers.unshift({
          username: this.formData.username,
          real_name: this.formData.real_name,
          type: adminType,
          created_at: new Date()
        })

        // Reset form
        this.resetForm()
      } catch (error) {
        this.errorMessage = error.data || 'Failed to create user'
      } finally {
        this.loading = false
      }
    },

    resetForm() {
      this.$refs.createUserForm.resetFields()
      this.formData = {
        username: '',
        password: '',
        real_name: '',
        userType: 'regular',
        openApi: false,
        twoFactorAuth: false
      }
      this.usernameValid = null
      this.passwordStrength = 0
    },

    handleUsernameChange(value) {
      if (!value) {
        this.usernameValid = null
        return
      }
      // Check username availability
      this.checkUsernameAvailability(value)
    },

    async checkUsernameAvailability(username) {
      try {
        const response = await api.checkUsername(username)
        this.usernameValid = !response.data.exists
      } catch (error) {
        this.usernameValid = null
      }
    },

    checkPasswordStrength(password) {
      let strength = 0
      if (password.length >= 6) strength++
      if (password.length >= 10) strength++
      if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++
      if (/[0-9]/.test(password)) strength++
      if (/[^a-zA-Z0-9]/.test(password)) strength++
      this.passwordStrength = strength
    },

    getUserIcon(type) {
      if (type === 'Admin') return 'md-build'
      if (type === 'Super Admin') return 'md-star'
      return 'ios-person'
    },

    getUserTagColor(type) {
      if (type === 'Admin') return 'blue'
      if (type === 'Super Admin') return 'gold'
      return 'default'
    },

    formatTime(date) {
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      if (minutes < 1) return 'just now'
      if (minutes < 60) return `${minutes}m ago`
      const hours = Math.floor(minutes / 60)
      if (hours < 24) return `${hours}h ago`
      return date.toLocaleDateString()
    }
  }
}
</script>

<style scoped lang="less">
.create-user-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.create-user-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  .card-header {
    text-align: center;
    padding: 20px 0;
    
    h2 {
      font-size: 24px;
      margin-bottom: 8px;
      color: #17233d;
    }
    
    p {
      color: #808695;
      font-size: 14px;
    }
  }
}

.password-strength {
  margin-top: 8px;
  
  .strength-text {
    font-size: 12px;
    color: #808695;
    margin-bottom: 4px;
  }
}

.button-group {
  display: flex;
  gap: 12px;
  
  button:last-child {
    flex: 1;
  }
}

.recent-users {
  h3 {
    font-size: 16px;
    margin-bottom: 16px;
    color: #17233d;
  }
}

// Responsive design
@media (max-width: 768px) {
  .create-user-container {
    padding: 10px;
  }
  
  .button-group {
    flex-direction: column;
    
    button {
      width: 100%;
    }
  }
}
</style>