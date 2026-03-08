<template>
  <section class="mb-5 lg:mb-6 xl:mb-8">
    <h2 class="text-xl font-medium leading-7 tracking-normal text-[#101828] m-0 mb-3 lg:mb-4">Create new project</h2>
    <div class="bg-white rounded-[10px] p-4 lg:p-5 xl:p-6 shadow-[0_4px_16px_rgba(0,0,0,0.08)]">
      <form @submit.prevent="handleSubmit" class="flex flex-col gap-3 xl:gap-4">
        <div class="flex flex-col gap-[0.375rem]">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-[#111827]" for="project-name">Project Name *</label>
            <span :class="name.length > 100 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">
              {{ name.length }}/100
            </span>
          </div>
          <input
            id="project-name"
            v-model="name"
            type="text"
            placeholder="My Project"
            required
            :class="name.length > 100 ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
            class="py-[0.6rem] px-3 rounded-md text-[0.9375rem] text-[#111827] bg-[hsl(var(--background))] transition focus:outline-none focus:bg-white"
          />
          <p v-if="name.length > 100" class="text-xs text-[#ef4444] m-0">
            Project name must not exceed 100 characters.
          </p>
        </div>
        <div class="flex flex-col gap-[0.375rem]">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-[#111827]" for="project-desc">Description (optional)</label>
            <span :class="description.length > 500 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">
              {{ description.length }}/500
            </span>
          </div>
          <textarea
            id="project-desc"
            v-model="description"
            placeholder="Brief description of this project"
            rows="3"
            :class="description.length > 500 ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
            class="py-[0.6rem] px-3 rounded-md text-[0.9375rem] text-[#111827] bg-[hsl(var(--background))] resize-none min-h-[80px] transition focus:outline-none focus:bg-white font-[inherit] overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          ></textarea>
          <p v-if="description.length > 500" class="text-xs text-[#ef4444] m-0">
            Description must not exceed 500 characters.
          </p>
        </div>
        <div v-if="error" class="text-[0.8125rem] text-[#ef4444]">{{ error }}</div>
        <div class="flex justify-end pt-1">
          <button
            type="submit"
            :disabled="isCreating || !name.trim() || name.length > 100 || description.length > 500"
            class="inline-flex items-center justify-center gap-[10px] h-[33px] px-5 py-0.5 bg-[#4954E7] hover:bg-[#3a44d4] text-white text-sm font-normal rounded-[10px] border-none cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >{{ isCreating ? 'Creating…' : 'Create project' }}</button>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createProject } from '@/api/projects'
import { showToast } from '@/lib/toast'

const emit = defineEmits<{
  created: []
}>()

const name = ref('')
const description = ref('')
const isCreating = ref(false)
const error = ref<string | null>(null)

const handleSubmit = async () => {
  if (!name.value.trim() || name.value.length > 100 || description.value.length > 500) return

  isCreating.value = true
  error.value = null
  try {
    await createProject({
      name: name.value.trim(),
      description: description.value.trim() || undefined,
    })
    name.value = ''
    description.value = ''
    showToast('Project created successfully')
    emit('created')
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to create project'
  } finally {
    isCreating.value = false
  }
}
</script>
