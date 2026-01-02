<!-- frontend/src/App.vue -->
<template>
  <div v-if="!authStore.isAuthenticated.value">
    <LoginPage
      v-if="showLogin"
      @switch-to-register="showLogin = false"
      @login-success="handleAuthSuccess"
    />
    <RegisterPage
      v-else
      @switch-to-login="showLogin = true"
      @register-success="handleAuthSuccess"
    />
  </div>
  <div v-else>
    <div class="navbar">
      <div class="navbar-content">
        <h2 class="navbar-title">Image Stitch Generator</h2>
        <div class="navbar-actions">
          <span class="user-name">{{ authStore.state.user?.name }}</span>
          <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>
      </div>
    </div>
    <HomePage />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import HomePage from './pages/HomePage.vue'
import LoginPage from './pages/LoginPage.vue'
import RegisterPage from './pages/RegisterPage.vue'
import { authStore } from './stores/authStore'
import { getCurrentUser } from './api/auth'

const showLogin = ref(true)

const handleAuthSuccess = async () => {
  try {
    const user = await getCurrentUser()
    authStore.setUser(user)
  } catch (e) {
    console.error('Failed to get user info', e)
  }
}

const handleLogout = () => {
  authStore.logout()
  showLogin.value = true
}

onMounted(async () => {
  if (authStore.isAuthenticated.value) {
    try {
      const user = await getCurrentUser()
      authStore.setUser(user)
    } catch (e) {
      console.error('Failed to get user info', e)
      authStore.logout()
    }
  }
})
</script>

<style>
.navbar {
  background: white;
  border-bottom: 1px solid #e5e5e5;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-title {
  margin: 0;
  font-size: 1.25rem;
  color: #1a1a1a;
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-name {
  color: #666;
  font-weight: 500;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #e5e5e5;
}
</style>
