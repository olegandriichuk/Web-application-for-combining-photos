<template>
  <div class="max-w-[1392px] mx-auto w-full py-5 px-4 pb-10 lg:py-6 lg:px-5 lg:pb-12 xl:py-8 xl:px-6 xl:pb-16 min-h-screen box-border text-[#111827]">

    <!-- ── Page header ─────────────────────────────────────────── -->
    <header class="grid grid-cols-[1fr_auto_1fr] items-center mb-6 lg:mb-7 xl:mb-10">
      <h1 class="col-start-2 m-0 text-lg lg:text-xl xl:text-[1.375rem] font-bold text-[#111827] text-center">Main page</h1>
      <div class="col-start-3 flex gap-2 justify-end items-center">
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
    </header>

    <CreateProjectForm @created="loadProjects" />

    <ProjectList
      :projects="projects"
      :is-loading="isLoading"
      :error="error"
      :latest-jobs="latestJobs"
      :latest-finished-jobs="latestFinishedJobs"
      @open-workspace="openWorkspace"
      @open-history="openHistory"
      @cancel-job="handleCancelJob"
      @delete-project="handleDeleteProject"
    />

  </div>

  <ConfirmModal
    v-if="pendingDeleteProject"
    title="Delete Project"
    description="Are you sure you want to delete this project? All associated photos and data will be permanently removed."
    confirm-label="Delete Project"
    @confirm="confirmDeleteProject"
    @cancel="pendingDeleteProject = null"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Settings, LogOut } from 'lucide-vue-next'
import { authStore } from '@/stores/authStore'
import { listProjects, deleteProject, type Project } from '../../api/projects'
import { listStitchJobs, cancelStitchJob } from '../../api/stitchJobs'
import { showToast } from '@/lib/toast'
import { type StitchJob } from '../../types/stitchJob'
import CreateProjectForm from '../../components/CreateProjectForm.vue'
import ProjectList from '../../components/ProjectList.vue'
import ConfirmModal from '../../components/ConfirmModal.vue'

const router = useRouter()

const projects = ref<Project[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

// projectId → latest StitchJob (null = loaded but no jobs, key absent = loading)
const latestJobs = ref<Record<string, StitchJob | null>>({})
// projectId → latest *finished* job (for download button)
const latestFinishedJobs = ref<Record<string, StitchJob | null>>({})

const handleGoToSettings = () => {
  // placeholder — wire up to router.push('/settings') when the page exists
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const loadLatestJobs = async () => {
  await Promise.allSettled(
    projects.value.map(async (project) => {
      try {
        const [latestResp, finishedResp] = await Promise.all([
          listStitchJobs(project.id, { limit: 1, sort: 'startDateDesc' }),
          listStitchJobs(project.id, { limit: 1, sort: 'startDateDesc', status: 'finished' }),
        ])
        latestJobs.value[project.id] = latestResp.items[0] ?? null
        latestFinishedJobs.value[project.id] = finishedResp.items[0] ?? null
      } catch {
        latestJobs.value[project.id] = null
        latestFinishedJobs.value[project.id] = null
      }
    })
  )
}

const loadProjects = async () => {
  isLoading.value = true
  error.value = null
  latestJobs.value = {}
  latestFinishedJobs.value = {}
  try {
    projects.value = await listProjects()
    await loadLatestJobs()
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load projects'
  } finally {
    isLoading.value = false
  }
}

const openWorkspace = (projectId: string) => {
  router.push(`/projects/${projectId}/workspace`)
}

const openHistory = (projectId: string) => {
  router.push(`/projects/${projectId}/history`)
}

const handleCancelJob = async (projectId: string, jobId: string) => {
  if (!confirm('Cancel this Exposea job?')) return
  try {
    const updated = await cancelStitchJob(projectId, jobId)
    latestJobs.value[projectId] = updated
  } catch (e: any) {
    alert('Failed to cancel job: ' + (e?.response?.data?.detail ?? e?.message))
  }
}

const pendingDeleteProject = ref<{ id: string; name: string } | null>(null)

const handleDeleteProject = (projectId: string, projectName: string) => {
  pendingDeleteProject.value = { id: projectId, name: projectName }
}

const confirmDeleteProject = async () => {
  const target = pendingDeleteProject.value
  pendingDeleteProject.value = null
  if (!target) return
  try {
    await deleteProject(target.id)
    projects.value = projects.value.filter(p => p.id !== target.id)
    showToast('Project deleted successfully')
  } catch (e: any) {
    console.error(e)
    alert('Failed to delete project: ' + (e?.response?.data?.detail ?? e?.message))
  }
}

onMounted(() => {
  loadProjects()
})
</script>
