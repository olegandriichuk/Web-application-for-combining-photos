// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <div class="min-h-screen [background:linear-gradient(112.87deg,#F9FAFB_0%,#F3F4F6_100%)]">

    <router-view />
    <ToastContainer />

  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from './stores/authStore'
import { getCurrentUser } from './api/auth'
import ToastContainer from './components/ToastContainer.vue'

const router = useRouter()

onMounted(async () => {
  if (authStore.isAuthenticated.value) {
    try {
      const user = await getCurrentUser()
      authStore.setUser(user)
    } catch (e) {
      console.error('Failed to get user info', e)
      authStore.logout()
      router.push('/login')
    }
  }
})
</script>
