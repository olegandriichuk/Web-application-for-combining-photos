<template>
  <div class="h-screen flex flex-col max-w-[90%] mx-auto w-full py-5 px-4 pb-10 lg:py-6 lg:px-5 lg:pb-12 xl:py-8 xl:px-6 xl:pb-16 box-border text-[#111827] overflow-hidden">

    <!-- Page header -->
    <header class="grid grid-cols-[1fr_auto_1fr] items-center mb-6 lg:mb-7 xl:mb-10">
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

    <CreateProjectForm @created="onProjectCreated" />

    <ProjectList
    class="flex-1 min-h-0"
      :projects="projects"
      :is-loading="isLoading"
      :error="error"
      :latest-jobs="latestJobs"
      :latest-finished-jobs="latestFinishedJobs"
      :search-query="searchQuery"
      :active-filter-count="activeFilterCount"
      @update:search-query="searchQuery = $event"
      @search="applySearch"
      @open-filters="filterDrawerOpen = true"
      @open-workspace="openWorkspace"
      @delete-project="handleDeleteProject"
      @manage-users="handleManageUsers"
      @edit-project="handleEditProject"
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

  <ManageUsersModal
    v-if="managingProject"
    :project-id="managingProject.id"
    :is-private="managingProject.is_private"
    :current-user-id="authStore.state.user?.id ?? ''"
    @close="managingProject = null"
  />

  <EditProjectModal
    v-if="editingProject"
    :project="editingProject"
    @updated="onProjectUpdated"
    @cancel="editingProject = null"
  />

  <FilterDrawer
    :open="filterDrawerOpen"
    :filters="appliedFilters"
    @close="filterDrawerOpen = false"
    @apply="onFiltersApplied"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Settings, LogOut } from 'lucide-vue-next'
import { authStore } from '@/stores/authStore'
import { listProjects, deleteProject, type Project, type ProjectFilters } from '../../api/projects'
import { listStitchJobs } from '../../api/stitchJobs'
import { showToast } from '@/lib/toast'
import { type StitchJob } from '../../types/stitchJob'
import CreateProjectForm from '../../components/CreateProjectForm.vue'
import ProjectList from '../../components/ProjectList.vue'
import ConfirmModal from '../../components/ConfirmModal.vue'
import ManageUsersModal from '../../components/ManageUsersModal.vue'
import EditProjectModal from '../../components/EditProjectModal.vue'
import FilterDrawer from '../../components/FilterDrawer.vue'

const router = useRouter()

const projects = ref<Project[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const appliedFilters = ref<ProjectFilters>({})
const filterDrawerOpen = ref(false)

// projectId → latest StitchJob (null = loaded but no jobs, key absent = loading)
const latestJobs = ref<Record<string, StitchJob | null>>({})
const latestFinishedJobs = ref<Record<string, StitchJob | null>>({})

const activeFilterCount = computed(() => {
  const f = appliedFilters.value
  return (f.conditions?.length ?? 0) + (f.is_private !== undefined ? 1 : 0)
})

const managingProject = ref<Project | null>(null)
const editingProject = ref<Project | null>(null)

const handleGoToSettings = () => router.push('/settings')
const handleLogout = () => { authStore.logout(); router.push('/login') }

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
    projects.value = await listProjects(appliedFilters.value, searchQuery.value.trim())
    await loadLatestJobs()
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load projects'
  } finally {
    isLoading.value = false
  }
}

const applySearch = () => {
  loadProjects()
}

const onFiltersApplied = (filters: ProjectFilters) => {
  appliedFilters.value = filters
  loadProjects()
}

const openWorkspace = (projectId: string) => router.push(`/projects/${projectId}/workspace`)
const handleManageUsers = (projectId: string) => {
  managingProject.value = projects.value.find(p => p.id === projectId) ?? null
}

const handleEditProject = (projectId: string) => {
  const project = projects.value.find(p => p.id === projectId)
  if (project) editingProject.value = project
}

const onProjectUpdated = (updated: Project) => {
  const idx = projects.value.findIndex(p => p.id === updated.id)
  if (idx !== -1) projects.value[idx] = { ...projects.value[idx], ...updated }
  editingProject.value = null
}

const onProjectCreated = (project: Project) => {
  router.push(`/projects/${project.id}/workspace`)
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
