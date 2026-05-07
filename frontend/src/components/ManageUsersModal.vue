// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[9998] flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-[rgba(15,23,42,0.35)] backdrop-blur-[2px]"
        @click="emit('close')"
      />
      <!-- Card -->
      <div class="relative bg-white rounded-[14px] shadow-[0_20px_40px_rgba(15,23,42,0.15),0_1px_0_rgba(255,255,255,0.6)_inset] p-6 w-full max-w-[520px] max-h-[85vh] flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between mb-5">
          <h2 class="m-0 text-[15px] font-semibold text-[#0f172a]">Manage users</h2>
          <button
            type="button"
            class="w-7 h-7 flex items-center justify-center rounded-md text-[#6b7280] hover:bg-[#f1f5f9] transition-colors cursor-pointer border-none bg-transparent text-lg leading-none"
            @click="emit('close')"
          >✕</button>
        </div>

        <!-- Member list -->
        <div class="flex flex-col gap-2 overflow-y-auto mb-4 flex-1">
          <div
            v-for="member in members"
            :key="member.user_id"
            class="flex items-center gap-3 p-2 rounded-lg hover:bg-[#f9fafb]"
          >
            <!-- Avatar -->
            <div class="w-8 h-8 rounded-full bg-[#e0e7ff] text-[#4338ca] flex items-center justify-center text-[12px] font-semibold shrink-0">
              {{ member.user_name.charAt(0).toUpperCase() }}
            </div>
            <!-- Name + email -->
            <div class="flex-1 min-w-0">
              <div class="text-[13px] font-medium text-[#111827] truncate">{{ member.user_name }}</div>
              <div class="text-[11px] text-[#6b7280] truncate">{{ member.user_email }}</div>
            </div>
            <!-- Role badge / select -->
            <template v-if="member.role === 'owner'">
              <span :class="roleBadgeClass('owner')">Owner</span>
            </template>
            <template v-else>
              <select
                :value="member.role"
                class="text-[12px] border border-[#e5e7eb] rounded-md px-2 py-1 bg-white text-[#374151] cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                @change="handleRoleChange(member, ($event.target as HTMLSelectElement).value as 'editor' | 'viewer')"
              >
                <option value="editor">Editor</option>
                <option v-if="isPrivate" value="viewer">Viewer</option>
              </select>
              <!-- Remove button — hidden for own row -->
              <button
                v-if="member.user_id !== currentUserId"
                type="button"
                class="text-[12px] text-[#dc2626] hover:text-[#b91c1c] cursor-pointer border-none bg-transparent px-1 py-1 rounded transition-colors"
                @click="handleRemove(member)"
              >Remove</button>
            </template>
          </div>
          <div v-if="members.length === 0" class="text-[13px] text-[#9ca3af] text-center py-3">No members yet.</div>
        </div>

        <!-- Divider -->
        <div class="border-t border-[#e5e7eb] mb-4" />

        <!-- Add member form -->
        <div class="flex gap-2">
          <input
            v-model="addEmail"
            type="email"
            placeholder="Email address"
            class="flex-1 text-[13px] border border-[#e5e7eb] rounded-md px-3 py-[7px] focus:outline-none focus:ring-1 focus:ring-[#3b82f6] placeholder:text-[#9ca3af]"
            @keydown.enter="handleAddMember"
          />
          <select
            v-model="addRole"
            class="text-[13px] border border-[#e5e7eb] rounded-md px-2 py-[7px] bg-white text-[#374151] cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
          >
            <option value="editor">Editor</option>
            <option v-if="isPrivate" value="viewer">Viewer</option>
          </select>
          <button
            type="button"
            :disabled="isAdding"
            class="text-[13px] font-medium px-3 py-[7px] bg-[#111827] text-white rounded-md cursor-pointer hover:bg-[#1f2937] transition-colors disabled:opacity-50 disabled:cursor-not-allowed border-none"
            @click="handleAddMember"
          >{{ isAdding ? 'Adding…' : 'Add' }}</button>
        </div>
        <div v-if="addError" class="mt-2 text-[12px] text-[#dc2626]">{{ addError }}</div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listMembers, addMember, updateMemberRole, removeMember } from '@/api/projectMembers'
import { showToast } from '@/lib/toast'
import type { ProjectMember } from '@/types/projectMember'

const props = defineProps<{
  projectId: string
  currentUserId: string
  isPrivate: boolean
}>()

const emit = defineEmits<{ close: [] }>()

const members = ref<ProjectMember[]>([])
const addEmail = ref('')
const addRole = ref<'editor' | 'viewer'>('editor')
const addError = ref<string | null>(null)
const isAdding = ref(false)

const roleBadgeClass = (role: string): string => {
  const map: Record<string, string> = {
    owner: 'inline-flex items-center py-[0.2rem] px-[0.6rem] bg-[#f3f4f6] text-[#6b7280] border border-[#e5e7eb] rounded-full text-[0.7rem] font-medium',
    editor: 'inline-flex items-center py-[0.2rem] px-[0.6rem] bg-[#eff6ff] text-[#2563eb] border border-[#bfdbfe] rounded-full text-[0.7rem] font-medium',
    viewer: 'inline-flex items-center py-[0.2rem] px-[0.6rem] bg-[#f0fdf4] text-[#16a34a] border border-[#bbf7d0] rounded-full text-[0.7rem] font-medium',
  }
  return map[role] ?? ''
}

const loadMembers = async () => {
  try {
    members.value = await listMembers(props.projectId)
  } catch (e: any) {
    console.error('Failed to load members:', e)
  }
}

const handleAddMember = async () => {
  addError.value = null
  const email = addEmail.value.trim()
  if (!email) return

  // Client-side email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    addError.value = 'Please enter a valid email address'
    return
  }

  isAdding.value = true
  try {
    const member = await addMember(props.projectId, { email, role: addRole.value })
    members.value.push(member)
    addEmail.value = ''
    showToast('Member added')
  } catch (e: any) {
    addError.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to add member'
  } finally {
    isAdding.value = false
  }
}

const handleRoleChange = async (member: ProjectMember, newRole: 'editor' | 'viewer') => {
  const originalRole = member.role
  member.role = newRole
  try {
    await updateMemberRole(props.projectId, member.user_id, { role: newRole })
  } catch (e: any) {
    member.role = originalRole
    console.error('Failed to update role:', e)
  }
}

const handleRemove = async (member: ProjectMember) => {
  try {
    await removeMember(props.projectId, member.user_id)
    members.value = members.value.filter(m => m.user_id !== member.user_id)
    showToast('Member removed')
  } catch (e: any) {
    console.error('Failed to remove member:', e)
  }
}

onMounted(() => {
  loadMembers()
})
</script>
