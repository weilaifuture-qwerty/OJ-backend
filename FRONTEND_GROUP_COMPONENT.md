# Frontend Component for Group-Based Student Selection

The backend APIs are ready, but the frontend needs a component with group filtering. Here's an example Vue component that can be integrated:

## Enhanced Student Selector Component

```vue
<template>
  <div class="student-selector">
    <!-- Group Filter Dropdown -->
    <Select v-model="selectedGroup" 
            placeholder="Filter by group/class" 
            clearable
            style="width: 200px; margin-bottom: 10px;">
      <Option value="" label="All Students"></Option>
      <Option v-for="group in availableGroups" 
              :key="group" 
              :value="group" 
              :label="group"></Option>
    </Select>

    <!-- Search Input -->
    <Input v-model="searchQuery" 
           placeholder="Search students..." 
           search
           style="width: 300px; margin-bottom: 10px;" />

    <!-- Students Table or Transfer Component -->
    <Transfer
      :data="studentList"
      :target-keys="selectedStudentIds"
      :render-format="renderStudent"
      :titles="['Available Students', 'Selected Students']"
      filterable
      :filter-placeholder="'Search students'"
      @on-change="handleStudentChange"
      style="text-align: left;"
    >
      <div slot-scope="{ item }" class="student-item">
        <span class="student-name">{{ item.username }}</span>
        <span class="student-info">{{ item.real_name || 'N/A' }}</span>
        <Tag v-if="item.student_group" color="blue" size="small">{{ item.student_group }}</Tag>
      </div>
    </Transfer>

    <!-- Quick Actions -->
    <div class="quick-actions" style="margin-top: 10px;">
      <Button @click="selectAllInGroup" 
              :disabled="!selectedGroup"
              type="primary" 
              size="small">
        Select All in Group
      </Button>
      <Button @click="clearSelection" 
              type="default" 
              size="small">
        Clear Selection
      </Button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StudentGroupSelector',
  data() {
    return {
      selectedGroup: '',
      searchQuery: '',
      availableGroups: [],
      allStudents: [],
      selectedStudentIds: []
    }
  },
  computed: {
    studentList() {
      let students = this.allStudents;
      
      // Filter by group
      if (this.selectedGroup) {
        students = students.filter(s => s.student_group === this.selectedGroup);
      }
      
      // Filter by search
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        students = students.filter(s => 
          s.username.toLowerCase().includes(query) ||
          (s.real_name && s.real_name.toLowerCase().includes(query)) ||
          (s.email && s.email.toLowerCase().includes(query))
        );
      }
      
      // Format for Transfer component
      return students.map(s => ({
        key: s.id,
        label: `${s.username} (${s.real_name || 'N/A'})`,
        disabled: false,
        ...s
      }));
    }
  },
  methods: {
    async loadGroups() {
      try {
        const res = await this.$http.get('/api/available_groups');
        this.availableGroups = res.data.groups || [];
      } catch (error) {
        this.$error('Failed to load groups');
      }
    },
    
    async loadStudents() {
      try {
        // Use the enhanced available_students endpoint
        const params = {
          search: this.searchQuery,
          group: this.selectedGroup
        };
        
        const res = await this.$http.get('/api/available_students', { params });
        this.allStudents = res.data || [];
      } catch (error) {
        // Fallback to users endpoint if available_students fails
        try {
          const res = await this.$http.get('/api/users', { 
            params: { type: 'student' } 
          });
          this.allStudents = res.data || [];
        } catch (err) {
          this.$error('Failed to load students');
        }
      }
    },
    
    renderStudent(item) {
      return item.label;
    },
    
    handleStudentChange(targetKeys) {
      this.selectedStudentIds = targetKeys;
      this.$emit('change', targetKeys);
    },
    
    selectAllInGroup() {
      if (!this.selectedGroup) return;
      
      const groupStudentIds = this.allStudents
        .filter(s => s.student_group === this.selectedGroup)
        .map(s => s.id);
      
      // Add to existing selection
      this.selectedStudentIds = [...new Set([...this.selectedStudentIds, ...groupStudentIds])];
      this.$emit('change', this.selectedStudentIds);
    },
    
    clearSelection() {
      this.selectedStudentIds = [];
      this.$emit('change', []);
    }
  },
  watch: {
    selectedGroup() {
      this.loadStudents();
    },
    searchQuery() {
      // Debounce search
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.loadStudents();
      }, 300);
    }
  },
  mounted() {
    this.loadGroups();
    this.loadStudents();
  }
}
</script>

<style scoped>
.student-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.student-name {
  font-weight: 500;
}

.student-info {
  color: #666;
  font-size: 12px;
}

.quick-actions {
  display: flex;
  gap: 10px;
}
</style>
```

## Alternative: Using Students By Group View

```vue
<template>
  <div class="group-student-selector">
    <Tabs v-model="activeTab">
      <TabPane v-for="group in studentGroups" 
               :key="group.name" 
               :label="`${group.name} (${group.students.length})`"
               :name="group.name">
        <CheckboxGroup v-model="selectedStudents[group.name]" @on-change="updateSelection">
          <div v-for="student in group.students" 
               :key="student.id" 
               class="student-checkbox">
            <Checkbox :label="student.id">
              <span class="student-label">
                {{ student.username }} - {{ student.real_name || 'N/A' }}
                <Tag v-if="student.email" color="default" size="small">{{ student.email }}</Tag>
              </span>
            </Checkbox>
          </div>
        </CheckboxGroup>
      </TabPane>
    </Tabs>
    
    <div class="selection-summary">
      Total selected: {{ totalSelected }} students
    </div>
  </div>
</template>

<script>
export default {
  name: 'GroupBasedStudentSelector',
  data() {
    return {
      activeTab: '',
      studentGroups: [],
      selectedStudents: {}
    }
  },
  computed: {
    totalSelected() {
      return Object.values(this.selectedStudents)
        .flat()
        .length;
    }
  },
  methods: {
    async loadStudentsByGroup() {
      try {
        const res = await this.$http.get('/api/students_by_group');
        this.studentGroups = res.data.groups || [];
        
        // Initialize selected students object
        this.studentGroups.forEach(group => {
          this.$set(this.selectedStudents, group.name, []);
        });
        
        // Set first tab as active
        if (this.studentGroups.length > 0) {
          this.activeTab = this.studentGroups[0].name;
        }
      } catch (error) {
        this.$error('Failed to load students by group');
      }
    },
    
    updateSelection() {
      // Flatten all selected student IDs
      const allSelected = Object.values(this.selectedStudents).flat();
      this.$emit('change', allSelected);
    },
    
    selectAllInCurrentGroup() {
      const currentGroup = this.studentGroups.find(g => g.name === this.activeTab);
      if (currentGroup) {
        this.selectedStudents[this.activeTab] = currentGroup.students.map(s => s.id);
        this.updateSelection();
      }
    },
    
    clearCurrentGroup() {
      this.selectedStudents[this.activeTab] = [];
      this.updateSelection();
    }
  },
  mounted() {
    this.loadStudentsByGroup();
  }
}
</script>

<style scoped>
.student-checkbox {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.student-checkbox:last-child {
  border-bottom: none;
}

.student-label {
  margin-left: 8px;
}

.selection-summary {
  margin-top: 16px;
  padding: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  text-align: center;
}
</style>
```

## Integration Steps

1. Replace the basic student selector in your homework creation form with one of these components
2. Update the parent component to handle the selected student IDs
3. When creating homework, pass the selected student IDs to the API

## Usage in Parent Component

```javascript
// In your homework creation component
<StudentGroupSelector @change="handleStudentSelection" />

// In methods
handleStudentSelection(studentIds) {
  this.formData.student_ids = studentIds;
}

// When creating homework
async createHomework() {
  const data = {
    title: this.formData.title,
    description: this.formData.description,
    due_date: this.formData.due_date,
    problem_ids: this.formData.problem_ids,
    student_ids: this.formData.student_ids, // Selected students
    auto_grade: this.formData.auto_grade
  };
  
  await this.$http.post('/api/admin_create_homework', data);
}
```

## Backend APIs Used

- `GET /api/available_groups` - Get list of student groups
- `GET /api/available_students?group=GROUP_NAME` - Get students filtered by group
- `GET /api/students_by_group` - Get all students organized by groups
- `GET /api/users?type=student` - Alternative endpoint for all students

These components provide:
1. Group filtering dropdown
2. Search functionality
3. Bulk selection by group
4. Visual indicators for student groups
5. Better UX for managing large numbers of students