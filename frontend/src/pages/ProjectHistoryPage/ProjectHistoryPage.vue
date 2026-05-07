// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <div class="py-12 px-4 pb-16">
    <div class="max-w-90% mx-auto mb-7">
      <div class="flex items-center justify-between mb-[14px]">
        <button
          @click="goBackToProjects"
          class="px-[14px] py-[6px] bg-white/85 text-[#475569] border border-[rgba(15,23,42,0.12)] rounded-lg text-[13px] font-medium cursor-pointer hover:bg-[#f1f5f9] transition-colors"
        >←</button>
        <div class="flex gap-2 items-center">
          <button
            v-if="project?.role !== 'viewer'"
            title="Workspace"
            @click="goToWorkspace"
            class="w-9 h-9 flex items-center justify-center bg-white border border-[#e5e7eb] rounded-md cursor-pointer text-[#6b7280] shadow-sm hover:shadow-md hover:text-[#111827] transition-shadow p-0"
          >
            <LayoutGrid :size="16" aria-hidden="true" />
          </button>
          <button
            title="Settings"
            @click="handleGoToSettings"
            class="w-9 h-9 flex items-center justify-center bg-white border border-[#e5e7eb] rounded-md cursor-pointer text-[#6b7280] shadow-sm hover:shadow-md hover:text-[#111827] transition-shadow p-0"
          >
            <Settings :size="16" aria-hidden="true" />
          </button>
          <button
            title="Logout"
            @click="handleLogout"
            class="w-9 h-9 flex items-center justify-center bg-white border border-[#e5e7eb] rounded-md cursor-pointer text-[#6b7280] shadow-sm hover:shadow-md hover:text-[#111827] transition-shadow p-0"
          >
            <LogOut :size="16" aria-hidden="true" />
          </button>
        </div>
      </div>
      <h1 class="m-0 mb-1 text-xl font-bold text-[#0f172a]">
        {{ project?.name || 'Loading...' }} - Job History
      </h1>
      <p v-if="project?.description" class="m-0 text-[13px] text-[#64748b]">{{ project.description }}</p>
    </div>

    <div
      v-if="projectError"
      class="max-w-[1392px] mx-auto mt-3 text-[13px] text-[#ef4444] font-semibold bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] px-3 py-[10px] rounded-xl"
    >{{ projectError }}</div>

    <StitchJobHistory :project-id="projectId" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Settings, LogOut, LayoutGrid } from 'lucide-vue-next'
import { authStore } from '@/stores/authStore'
import { getProject, type Project } from '../../api/projects'
import StitchJobHistory from '../../components/StitchJobHistory.vue'

const route = useRoute()
const router = useRouter()

const projectId = ref<string>(route.params.projectId as string)
const project = ref<Project | null>(null)
const projectError = ref<string | null>(null)

const loadProject = async () => {
  try {
    project.value = await getProject(projectId.value)
  } catch (e: any) {
    console.error(e)
    projectError.value = 'Failed to load project'
  }
}

const goBackToProjects = () => router.push('/projects')
const goToWorkspace = () => router.push(`/projects/${projectId.value}/workspace`)

const handleGoToSettings = () => {
  router.push('/settings')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadProject()
})
</script>
