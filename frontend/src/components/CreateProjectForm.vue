// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <section class="mb-5 lg:mb-6 xl:mb-8">
    <!-- Card — matches project card dimensions -->
    <div class="relative bg-white rounded-[10px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] overflow-hidden flex items-center px-5 py-4 ">
      <button
        type="button"
        class="h-[30px] px-4 rounded-md bg-white hover:bg-[#f3f4f6] text-[#374151] text-[13px] font-medium transition-colors cursor-pointer border border-[#e5e7eb] whitespace-nowrap"
        @click="open = true"
      >+ Create project</button>
    </div>
  </section>

  <!-- Modal -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
        @click.self="closeModal"
      >
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-[540px] max-h-[90vh] overflow-y-auto">

          <!-- Modal header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-[#e5e7eb] sticky top-0 bg-white z-10">
            <h2 class="m-0 text-base font-semibold text-[#111827]">Create new project</h2>
            <button
              type="button"
              class="w-7 h-7 flex items-center justify-center rounded-lg text-[#6b7280] hover:bg-[#f3f4f6] transition-colors text-[18px] leading-none"
              @click="closeModal"
            >×</button>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleSubmit" class="flex flex-col gap-4 px-6 py-5">

            <!-- Name -->
            <div class="flex flex-col gap-[0.375rem]">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-[#111827]" for="cp-name">Project Name *</label>
                <span :class="name.length > 100 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">{{ name.length }}/100</span>
              </div>
              <input
                id="cp-name"
                v-model="name"
                type="text"
                placeholder="My Project"
                required
                :class="nameError ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
                class="py-[0.6rem] px-3 rounded-md border text-[0.9375rem] text-[#111827] bg-white transition focus:outline-none"
              />
              <p v-if="nameError" class="text-xs text-[#ef4444] m-0">{{ nameError }}</p>
            </div>

            <!-- Description -->
            <div class="flex flex-col gap-[0.375rem]">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-[#111827]" for="cp-desc">Description</label>
                <span :class="description.length > 500 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">{{ description.length }}/500</span>
              </div>
              <textarea
                id="cp-desc"
                v-model="description"
                placeholder="Brief description of this project"
                rows="3"
                :class="description.length > 500 ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
                class="py-[0.6rem] px-3 rounded-md border text-[0.9375rem] text-[#111827] bg-white resize-none min-h-[80px] transition focus:outline-none font-[inherit] overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
              ></textarea>
              <p v-if="description.length > 500" class="text-xs text-[#ef4444] m-0">Must not exceed 500 characters.</p>
            </div>

            <!-- Region + Year -->
            <div class="grid grid-cols-2 gap-3">
              <div class="flex flex-col gap-[0.375rem]">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-[#111827]" for="cp-region">Region</label>
                  <span v-if="region.length > 0" :class="region.length > 100 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">{{ region.length }}/100</span>
                </div>
                <input
                  id="cp-region"
                  v-model="region"
                  type="text"
                  placeholder="e.g. South Moravia"
                  :class="region.length > 100 ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
                  class="py-[0.6rem] px-3 rounded-md border text-[0.9375rem] text-[#111827] bg-white transition focus:outline-none"
                />
                <p v-if="region.length > 100" class="text-xs text-[#ef4444] m-0">Must not exceed 100 characters.</p>
              </div>
              <div class="flex flex-col gap-[0.375rem]">
                <label class="text-sm font-medium text-[#111827]" for="cp-year">Year</label>
                <input
                  id="cp-year"
                  v-model.number="year"
                  type="number"
                  placeholder="e.g. 2023"
                  class="py-[0.6rem] px-3 rounded-md border border-[#e5e7eb] text-[0.9375rem] text-[#111827] bg-white transition focus:outline-none focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]"
                />
              </div>
            </div>

            <!-- Document type + Institution -->
            <div class="grid grid-cols-2 gap-3">
              <div class="flex flex-col gap-[0.375rem]">
                <label class="text-sm font-medium text-[#111827]" for="cp-doctype">Document Type</label>
                <select
                  id="cp-doctype"
                  v-model="documentType"
                  class="py-[0.6rem] px-3 rounded-md border border-[#e5e7eb] text-[0.9375rem] text-[#111827] bg-white transition focus:outline-none focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]"
                >
                  <option value="">— select —</option>
                  <option v-for="dt in DOCUMENT_TYPES" :key="dt" :value="dt">{{ dt }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-[0.375rem]">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-[#111827]" for="cp-institution">Institution</label>
                  <span v-if="institution.length > 0" :class="institution.length > 100 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">{{ institution.length }}/100</span>
                </div>
                <input
                  id="cp-institution"
                  v-model="institution"
                  type="text"
                  placeholder="e.g. National Archive"
                  :class="institution.length > 100 ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
                  class="py-[0.6rem] px-3 rounded-md border text-[0.9375rem] text-[#111827] bg-white transition focus:outline-none"
                />
                <p v-if="institution.length > 100" class="text-xs text-[#ef4444] m-0">Must not exceed 100 characters.</p>
              </div>
            </div>

            <!-- Collection + Privacy -->
            <div class="grid grid-cols-2 gap-3">
              <div class="flex flex-col gap-[0.375rem]">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-[#111827]" for="cp-collection">Collection</label>
                  <span v-if="collection.length > 0" :class="collection.length > 100 ? 'text-[#ef4444]' : 'text-[#9ca3af]'" class="text-xs">{{ collection.length }}/100</span>
                </div>
                <input
                  id="cp-collection"
                  v-model="collection"
                  type="text"
                  placeholder="e.g. Czech topographic"
                  :class="collection.length > 100 ? 'border-[#ef4444] focus:border-[#ef4444] focus:shadow-[0_0_0_3px_rgba(239,68,68,0.15)]' : 'border-[#e5e7eb] focus:border-[#3b82f6] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'"
                  class="py-[0.6rem] px-3 rounded-md border text-[0.9375rem] text-[#111827] bg-white transition focus:outline-none"
                />
                <p v-if="collection.length > 100" class="text-xs text-[#ef4444] m-0">Must not exceed 100 characters.</p>
              </div>
              <div class="flex flex-col gap-[0.375rem] justify-end">
                <label class="flex items-center gap-2 cursor-pointer select-none py-[0.6rem]">
                  <div
                    class="relative w-9 h-5 rounded-full transition-colors"
                    :class="isPrivate ? 'bg-[#4954E7]' : 'bg-[#d1d5db]'"
                    @click="isPrivate = !isPrivate"
                  >
                    <div
                      class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
                      :class="isPrivate ? 'translate-x-4' : 'translate-x-0'"
                    ></div>
                  </div>
                  <span class="text-sm text-[#111827]">Private</span>
                  <span class="relative group inline-flex items-center cursor-default">
                    <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                      <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
                    </svg>
                    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-[240px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
                      <div class="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-[#1e293b]"></div>
                      When private, only invited members can see and access this project. Public projects are visible to all users as viewers.
                    </div>
                  </span>
                </label>
              </div>
            </div>

            <div v-if="error" class="text-[0.8125rem] text-[#ef4444]">{{ error }}</div>

            <!-- Footer -->
            <div class="flex justify-end gap-2 pt-1">
              <button
                type="button"
                @click="closeModal"
                class="h-[33px] px-4 rounded-[10px] border border-[#e5e7eb] bg-white text-sm text-[#6b7280] hover:bg-[#f9fafb] transition-colors cursor-pointer"
              >Cancel</button>
              <button
                type="submit"
                :disabled="isCreating || !canSubmit"
                class="inline-flex items-center justify-center h-[33px] px-5 bg-[#4954E7] hover:bg-[#3a44d4] text-white text-sm rounded-[10px] border-none cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >{{ isCreating ? 'Creating…' : 'Create project' }}</button>
            </div>

          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { createProject, type Project } from '@/api/projects'
import { DOCUMENT_TYPES, type DocumentType } from '@/types/project'
import { showToast } from '@/lib/toast'

const emit = defineEmits<{ created: [project: Project] }>()

const open = ref(false)

const name = ref('')
const description = ref('')
const region = ref('')
const year = ref<number | ''>('')
const documentType = ref<DocumentType | ''>('')
const institution = ref('')
const collection = ref('')
const isPrivate = ref(false)
const isCreating = ref(false)
const error = ref<string | null>(null)

const nameError = computed(() => {
  if (name.value.length === 0) return null  // only shown after attempted submit
  if (name.value.trim().length === 0) return 'Project name cannot be empty.'
  if (name.value.length > 100) return 'Must not exceed 100 characters.'
  return null
})

const canSubmit = computed(() =>
  name.value.trim().length > 0 &&
  name.value.length <= 100 &&
  description.value.length <= 500 &&
  region.value.length <= 100 &&
  institution.value.length <= 100 &&
  collection.value.length <= 100
)

const resetForm = () => {
  name.value = ''
  description.value = ''
  region.value = ''
  year.value = ''
  documentType.value = ''
  institution.value = ''
  collection.value = ''
  isPrivate.value = false
  error.value = null
}

const closeModal = () => {
  open.value = false
  resetForm()
}

const handleSubmit = async () => {
  if (!canSubmit.value) return
  isCreating.value = true
  error.value = null
  try {
    const project = await createProject({
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      region: region.value.trim() || undefined,
      year: year.value !== '' ? year.value : undefined,
      document_type: documentType.value !== '' ? documentType.value : undefined,
      institution: institution.value.trim() || undefined,
      collection: collection.value.trim() || undefined,
      is_private: isPrivate.value,
    })
    showToast('Project created successfully')
    closeModal()
    emit('created', project)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to create project'
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.18s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.18s ease;
}
.modal-enter-from .bg-white {
  transform: translateY(-8px);
}
</style>
