// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <div class="max-w-[640px] mx-auto w-full py-5 px-4 pb-10 lg:py-6 lg:px-5 lg:pb-12 xl:py-8 xl:px-6 xl:pb-16 min-h-screen box-border text-[#111827]">

    <!-- Page header -->
    <header class="grid grid-cols-[1fr_auto_1fr] items-center mb-8 lg:mb-10">
      <button
        title="Back"
        @click="router.back()"
        class="w-9 h-9 flex items-center justify-center bg-white border border-[#e5e7eb] rounded-md cursor-pointer text-[#6b7280] shadow-sm hover:shadow-md hover:text-[#111827] transition-shadow p-0"
      >
        <ArrowLeft :size="16" aria-hidden="true" />
      </button>
      <h1 class="col-start-2 m-0 text-lg lg:text-xl xl:text-[1.375rem] font-bold text-[#111827] text-center">Account Settings</h1>
      <div class="col-start-3 flex gap-2 justify-end items-center">
        <button
          title="Logout"
          @click="handleLogout"
          class="w-9 h-9 flex items-center justify-center bg-white border border-[#e5e7eb] rounded-md cursor-pointer text-[#6b7280] shadow-sm hover:shadow-md hover:text-[#111827] transition-shadow p-0"
        >
          <LogOut :size="16" aria-hidden="true" />
        </button>
      </div>
    </header>

    <!-- Profile & password card -->
    <div class="bg-white border border-[#e5e7eb] rounded-xl shadow-sm p-6 lg:p-8 flex flex-col gap-5">

      <h2 class="m-0 text-base font-semibold text-[#111827]">Profile Information</h2>

      <form @submit.prevent="handleSave" novalidate class="flex flex-col gap-4">

        <!-- Username -->
        <div class="flex flex-col gap-1.5">
          <Label for="name" class="font-normal">Username</Label>
          <Input
            id="name"
            v-model="name"
            type="text"
            placeholder="Your username"
            autocomplete="username"
          />
          <p v-if="nameError" class="m-0 text-sm text-[#ef4444]">{{ nameError }}</p>
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

        <!-- Divider -->
        <div class="border-t border-[#e5e7eb] my-1" />

        <h2 class="m-0 text-base font-semibold text-[#111827]">Change Password</h2>
        <p class="m-0 text-sm text-[#6b7280] -mt-2">Leave blank to keep your current password.</p>

        <!-- New password -->
        <div class="flex flex-col gap-1.5">
          <Label for="newPassword" class="font-normal">New password</Label>
          <Input
            id="newPassword"
            v-model="newPassword"
            type="password"
            placeholder="Enter new password"
            autocomplete="new-password"
          />
          <p v-if="newPasswordError" class="m-0 text-sm text-[#ef4444]">{{ newPasswordError }}</p>
        </div>

        <!-- Confirm new password -->
        <div class="flex flex-col gap-1.5">
          <Label for="confirmPassword" class="font-normal">Confirm new password</Label>
          <Input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Confirm new password"
            autocomplete="new-password"
          />
          <p v-if="confirmPasswordError" class="m-0 text-sm text-[#ef4444]">{{ confirmPasswordError }}</p>
        </div>

        <!-- API error -->
        <p v-if="saveError" class="m-0 text-sm text-[#ef4444]">{{ saveError }}</p>

        <!-- Save button -->
        <Button
          type="submit"
          :disabled="!isDirty || isSaving"
          class="w-full h-12 px-8 py-3 mt-1 bg-[#4954E7] hover:bg-[#3a44d4] text-white font-normal text-base rounded-[14px] border-none shadow-[0_4px_14px_rgba(73,84,231,0.25)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ isSaving ? 'Saving…' : 'Save Changes' }}
        </Button>

      </form>
    </div>

    <!-- Delete account card -->
    <div class="bg-white border border-[#fecaca] rounded-xl shadow-sm p-6 lg:p-8 flex flex-col gap-3 mt-6">
      <h2 class="m-0 text-base font-semibold text-[#111827]">Delete Account</h2>
      <p class="m-0 text-sm text-[#6b7280]">
        Permanently delete your account, all projects, photos, and stitch job history. This action cannot be undone.
      </p>
      <div>
        <button
          type="button"
          @click="pendingDelete = true"
          class="h-10 px-5 bg-[#ef4444] hover:bg-[#dc2626] text-white text-sm font-normal rounded-md border-none cursor-pointer transition-colors"
        >
          Delete Account
        </button>
      </div>
    </div>

  </div>

  <!-- Delete account confirmation modal -->
  <ConfirmModal
    v-if="pendingDelete"
    title="Delete Account"
    description="Are you sure you want to permanently delete your account? All your projects, photos, and stitch jobs will be removed. This cannot be undone."
    confirm-label="Delete Account"
    @confirm="confirmDeleteAccount"
    @cancel="pendingDelete = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, LogOut } from 'lucide-vue-next'
import { authStore } from '@/stores/authStore'
import { updateUser, deleteAccount, getCurrentUser } from '@/api/auth'
import { showToast } from '@/lib/toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import ConfirmModal from '@/components/ConfirmModal.vue'

const router = useRouter()

// ── Form state ──────────────────────────────────────────────────
const name = ref('')
const email = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// Original values to detect changes
const originalName = ref('')
const originalEmail = ref('')

const isSaving = ref(false)
const saveError = ref<string | null>(null)
const submitted = ref(false)
const emailExistsError = ref<string | null>(null)
const pendingDelete = ref(false)

// ── Seed form from current user ──────────────────────────────────
onMounted(async () => {
  let user = authStore.state.user
  if (!user) {
    try {
      user = await getCurrentUser()
      authStore.setUser(user)
    } catch {
      router.push('/login')
      return
    }
  }
  name.value = user.name
  email.value = user.email
  originalName.value = user.name
  originalEmail.value = user.email
})

// ── Dirty check ──────────────────────────────────────────────────
const isDirty = computed(() =>
  name.value !== originalName.value ||
  email.value !== originalEmail.value ||
  newPassword.value.length > 0
)

// ── Watchers to clear server errors on field change ──────────────
watch(email, () => { emailExistsError.value = null })
watch(saveError, () => {}, { flush: 'sync' }) // keeps reactivity

// ── Validation ───────────────────────────────────────────────────
const USERNAME_RE = /^[a-zA-Z0-9._]+$/

const nameError = computed(() => {
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

const newPasswordError = computed(() => {
  if (!submitted.value) return null
  if (!newPassword.value) return null // optional
  const p = newPassword.value
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
  if (!newPassword.value) return null // only validate if new password is set
  if (!confirmPassword.value) return 'Please confirm your new password.'
  if (newPassword.value !== confirmPassword.value) return 'Passwords do not match.'
  return null
})

const isFormValid = computed(() =>
  !nameError.value &&
  !emailError.value &&
  !newPasswordError.value &&
  !confirmPasswordError.value
)

// ── Save handler ─────────────────────────────────────────────────
const handleSave = async () => {
  submitted.value = true
  if (!isFormValid.value) return

  isSaving.value = true
  saveError.value = null

  const payload: { name?: string; email?: string; password?: string } = {}
  if (name.value !== originalName.value) payload.name = name.value
  if (email.value !== originalEmail.value) payload.email = email.value
  if (newPassword.value) payload.password = newPassword.value

  try {
    const result = await updateUser(payload)

    // Refresh auth store with updated user and new token
    authStore.setUser(result.user)
    authStore.setToken(result.access_token)

    originalName.value = result.user.name
    originalEmail.value = result.user.email
    newPassword.value = ''
    confirmPassword.value = ''
    submitted.value = false

    showToast('Account updated successfully')
  } catch (e: any) {
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
      saveError.value = detail || 'Failed to save changes.'
    }
  } finally {
    isSaving.value = false
  }
}

// ── Delete account ───────────────────────────────────────────────
const confirmDeleteAccount = async () => {
  try {
    await deleteAccount()
  } catch {
    // If the request fails the user is still logged in — show error
    pendingDelete.value = false
    showToast('Failed to delete account. Please try again.')
    return
  }
  authStore.logout()
  router.push('/login')
}

// ── Logout ───────────────────────────────────────────────────────
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
