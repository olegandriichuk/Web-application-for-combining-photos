<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-4 py-6 lg:py-8 xl:py-12 gap-6 xl:gap-[46px]">

    <!-- Page header -->
    <div class="flex flex-col items-center gap-3 w-full max-w-[564px]">
      <h1 class="text-xl font-medium text-[#111827] text-center tracking-tight">
        Sign In
      </h1>
      <p class="text-sm text-[#6b7280] text-center font-normal leading-relaxed">
        Sign in to continue creating beautiful blended images
      </p>
    </div>

    <Card class="w-full max-w-[564px] p-8">

      <!-- Form -->
      <form @submit.prevent="handleLogin" novalidate class="flex flex-col gap-5 xl:gap-6">

        <!-- Email -->
        <div class="flex flex-col gap-1.5">
          <Label for="email" class="font-normal">Email address</Label>
          <Input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <!-- Password -->
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <Label for="password" class="font-normal">Password</Label>
            
          </div>
          <Input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter your password"
            required
            autocomplete="current-password"
          />
        </div>

        <!-- Error message -->
        <p v-if="error" class="m-0 text-sm text-[#ef4444]">{{ error }}</p>

        <!-- Submit -->
        <Button
          type="submit"
          :disabled="isLoading"
          class="w-full h-14 px-8 py-4 gap-[10px] mt-3 xl:mt-4 bg-[#4954E7] hover:bg-[#3a44d4] text-white font-normal text-base rounded-[14px] border-none shadow-[0_4px_14px_rgba(73,84,231,0.25)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ isLoading ? 'Signing in…' : 'Sign In' }}
        </Button>

        <!-- Register link -->
        <p class="text-center text-sm text-[#6b7280]">
          Don't have an account?
          <a
            href="#"
            @click.prevent="goToRegister"
            class="font-normal text-[#3b82f6] hover:underline"
          >Sign Up</a>
        </p>

      </form>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login as apiLogin, getCurrentUser } from '../../api/auth'
import { authStore } from '../../stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'

const router = useRouter()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)

const handleLogin = async () => {
  isLoading.value = true
  error.value = null

  try {
    const tokenResponse = await apiLogin({
      email: email.value,
      password: password.value,
    })

    authStore.setToken(tokenResponse.access_token)

    const user = await getCurrentUser()
    authStore.setUser(user)

    router.push('/projects')
  } catch (e: any) {
    console.error(e)
    const status = e?.response?.status
    error.value = (status === 401 || status === 403)
      ? 'The login information entered is incorrect'
      : e?.response?.data?.detail ?? e?.message ?? 'Login failed'
  } finally {
    isLoading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>
