// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-4 py-6 lg:py-8 xl:py-12 gap-6 xl:gap-[46px]">

    <!-- Page header -->
    <div class="flex flex-col items-center gap-3 w-full max-w-[564px]">
      <h1 class="text-xl font-medium text-[#111827] text-center tracking-tight">
        Sign Up
      </h1>
      <p class="text-sm text-[#6b7280] text-center font-normal leading-relaxed">
        Sign up to start creating stitched images
      </p>
    </div>

    <Card class="w-full max-w-[564px] p-8">

      <!-- novalidate disables browser-native validation tooltips -->
      <form @submit.prevent="handleRegister" novalidate class="flex flex-col gap-5 xl:gap-6">

        <!-- Username -->
        <div class="flex flex-col gap-1.5">
          <Label for="name" class="font-normal">Username</Label>
          <Input
            id="name"
            v-model="name"
            type="text"
            placeholder="Enter your username"
            autocomplete="name"
          />
          <p v-if="usernameError" class="m-0 text-sm text-[#ef4444]">{{ usernameError }}</p>
        </div>

        <!-- Email -->
        <div class="flex flex-col gap-1.5">
          <Label for="email" class="font-normal">Email address</Label>
          <Input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            autocomplete="email"
          />
          <p v-if="emailError" class="m-0 text-sm text-[#ef4444]">{{ emailError }}</p>
          <p v-else-if="emailExistsError" class="m-0 text-sm text-[#ef4444]">{{ emailExistsError }}</p>
        </div>

        <!-- Password -->
        <div class="flex flex-col gap-1.5">
          <Label for="password" class="font-normal">Password</Label>
          <Input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter your password"
            autocomplete="new-password"
          />
          <p v-if="passwordError" class="m-0 text-sm text-[#ef4444]">{{ passwordError }}</p>
        </div>

        <!-- Confirm Password -->
        <div class="flex flex-col gap-1.5">
          <Label for="confirmPassword" class="font-normal">Confirm Password</Label>
          <Input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            autocomplete="new-password"
          />
          <p v-if="confirmPasswordError" class="m-0 text-sm text-[#ef4444]">{{ confirmPasswordError }}</p>
        </div>

        <!-- API error -->
        <p v-if="error" class="m-0 text-sm text-[#ef4444]">{{ error }}</p>

        <!-- Submit -->
        <Button
          type="submit"
          :disabled="isLoading"
          class="w-full h-14 px-8 py-4 gap-[10px] mt-3 xl:mt-4 bg-[#4954E7] hover:bg-[#3a44d4] text-white font-normal text-base rounded-[14px] border-none shadow-[0_4px_14px_rgba(73,84,231,0.25)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ isLoading ? 'Creating account…' : 'Sign Up' }}
        </Button>

        <!-- Login link -->
        <p class="text-center text-sm text-[#6b7280]">
          Already have an account?
          <a
            href="#"
            @click.prevent="goToLogin"
            class="font-normal text-[#3b82f6] hover:underline"
          >Sign in</a>
        </p>

      </form>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { register as apiRegister, login as apiLogin, getCurrentUser } from '../../api/auth'
import { authStore } from '../../stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'

const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const submitted = ref(false)
const emailExistsError = ref<string | null>(null)

watch(email, () => { emailExistsError.value = null })

const USERNAME_RE = /^[a-zA-Z0-9._]+$/

const usernameError = computed(() => {
  if (!submitted.value) return null
  if (!name.value) return 'Username is required.'
  if (!USERNAME_RE.test(name.value) || name.value.length > 30)
    return 'Username may contain only letters, numbers, periods, and underscores (max 30 characters).'
  return null
})

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const emailError = computed(() => {
  if (!submitted.value) return null
  if (!email.value) return 'Email is required.'
  if (!EMAIL_RE.test(email.value)) return 'Please enter a valid email address.'
  return null
})

const passwordError = computed(() => {
  if (!submitted.value) return null
  if (!password.value) return 'Password is required.'
  const p = password.value
  if (
    p.length < 8 ||
    !/[a-z]/.test(p) ||
    !/[A-Z]/.test(p) ||
    !/[0-9]/.test(p) ||
    !/[^a-zA-Z0-9]/.test(p)
  )
    return 'Password must be at least 8 characters and include an uppercase letter, lowercase letter, number, and special character.'
  return null
})

const confirmPasswordError = computed(() => {
  if (!submitted.value) return null
  if (!confirmPassword.value) return 'Please confirm your password.'
  if (password.value !== confirmPassword.value) return 'Passwords do not match.'
  return null
})

const isFormValid = computed(() =>
  !usernameError.value && !emailError.value && !passwordError.value && !confirmPasswordError.value
)

const handleRegister = async () => {
  submitted.value = true
  if (!isFormValid.value) return

  isLoading.value = true
  error.value = null

  try {
    await apiRegister({
      name: name.value,
      email: email.value,
      password: password.value,
    })

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
    const detail: string = e?.response?.data?.detail ?? e?.message ?? ''
    const status = e?.response?.status
    if (
      status === 409 ||
      (status === 400 && /already registered/i.test(detail)) ||
      /already exist/i.test(detail) ||
      /duplicate/i.test(detail)
    ) {
      emailExistsError.value = 'A user with this email already exists.'
    } else {
      error.value = detail || 'Registration failed'
    }
  } finally {
    isLoading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>
