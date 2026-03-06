<template>
  <div class="pp-page">

    <!-- ── Page header ─────────────────────────────────────────── -->
    <header class="pp-header">
      <h1 class="pp-title">Main page</h1>
      <div class="pp-header-actions">
        <button class="pp-icon-btn" title="Settings">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- ── Create new project ────────────────────────────────────── -->
    <section class="pp-section">
      <h2 class="pp-section-title">Create new project</h2>
      <div class="pp-card">
        <form @submit.prevent="handleCreateProject" class="pp-create-form">
          <div class="pp-form-group">
            <label class="pp-label" for="project-name">Project Name *</label>
            <input
              id="project-name"
              v-model="newProjectName"
              type="text"
              placeholder="My Project"
              maxlength="200"
              required
              class="pp-input"
            />
          </div>
          <div class="pp-form-group">
            <label class="pp-label" for="project-desc">Description (optional)</label>
            <textarea
              id="project-desc"
              v-model="newProjectDescription"
              placeholder="Brief description of this project"
              maxlength="1000"
              rows="3"
              class="pp-input pp-textarea"
            ></textarea>
          </div>
          <div v-if="createError" class="pp-inline-error">{{ createError }}</div>
          <div class="pp-form-footer">
            <span class="pp-role-pill">Owner</span>
            <button
              type="submit"
              :disabled="isCreating || !newProjectName.trim()"
              class="pp-btn pp-btn-primary"
            >
              {{ isCreating ? 'Creating…' : 'Create project' }}
            </button>
          </div>
        </form>
      </div>
    </section>

    <!-- ── Loading / global error ────────────────────────────────── -->
    <div v-if="isLoading" class="pp-status pp-status-loading">Loading projects…</div>
    <div v-if="error" class="pp-status pp-status-error">{{ error }}</div>

    <!-- ── History ───────────────────────────────────────────────── -->
    <section class="pp-section" v-if="!isLoading && projects.length > 0">
      <h2 class="pp-section-title">History</h2>
      <div class="pp-projects">
        <article
          v-for="project in projects"
          :key="project.id"
          class="pp-card pp-project-card"
        >
          <!-- Header row -->
          <div class="pp-project-header">
            <h3 class="pp-project-name">{{ project.name }}</h3>
            <span class="pp-role-pill">Owner</span>
          </div>

          <!-- Description -->
          <p class="pp-project-desc">
            {{ project.description || 'No description' }}
          </p>

          <!-- Meta -->
          <div class="pp-project-meta">
            <span>{{ project.photo_count || 0 }} {{ project.photo_count === 1 ? 'image' : 'images' }}</span>
            <span>Created {{ formatDate(project.created_at) }}</span>
          </div>

          <!-- Actions -->
          <div class="pp-project-actions">
            <div class="pp-actions-group">
              <button
                class="pp-btn pp-btn-sm pp-btn-outline pp-btn-disabled"
                disabled
                title="Coming soon"
              >Manage users</button>
              <button
                class="pp-btn pp-btn-sm pp-btn-outline pp-btn-disabled"
                disabled
                title="Coming soon"
              >Preview of latest image</button>
              <button
                class="pp-btn pp-btn-sm pp-btn-outline"
                @click="openWorkspace(project.id)"
              >Open</button>

              <!-- Latest job status badge — navigates to history -->
              <template v-if="isJobLoaded(project.id)">
                <button
                  class="pp-btn pp-btn-sm pp-job-status"
                  :class="latestJobs[project.id]
                    ? `pp-job-status--${latestJobs[project.id]!.status}`
                    : 'pp-job-status--none'"
                  @click="openHistory(project.id)"
                  :title="latestJobs[project.id]
                    ? `Latest job: ${STATUS_LABELS[latestJobs[project.id]!.status]}`
                    : 'No Exposea jobs yet'"
                >
                  <span class="pp-job-status-dot" aria-hidden="true"></span>
                  {{ latestJobs[project.id]
                      ? STATUS_LABELS[latestJobs[project.id]!.status]
                      : 'No jobs' }}
                </button>
              </template>
              <!-- Skeleton while jobs are loading -->
              <span v-else class="pp-job-status-skeleton" aria-label="Loading job status"></span>
            </div>

            <div class="pp-actions-group">
              <!-- Cancel: only shown when job is queued or running -->
              <button
                v-if="latestJobs[project.id] && ['queued', 'running'].includes(latestJobs[project.id]!.status)"
                class="pp-btn pp-btn-sm pp-btn-outline pp-btn-cancel"
                @click="handleCancelJob(project.id, latestJobs[project.id]!.id)"
              >Cancel</button>
              <button
                class="pp-btn pp-btn-sm pp-btn-danger"
                @click="handleDeleteProject(project.id, project.name)"
              >Delete project</button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <!-- ── Empty state ───────────────────────────────────────────── -->
    <div class="pp-card pp-empty-state" v-else-if="!isLoading && !error">
      No projects yet. Create your first project above!
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  listProjects,
  createProject,
  deleteProject,
  type Project,
} from '../../api/projects'
import { listStitchJobs, cancelStitchJob } from '../../api/stitchJobs'
import { STATUS_LABELS, type StitchJob } from '../../types/stitchJob'
import './ProjectsPage.css'

const router = useRouter()

const projects = ref<Project[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const newProjectName = ref('')
const newProjectDescription = ref('')
const isCreating = ref(false)
const createError = ref<string | null>(null)

// projectId → latest StitchJob (null = loaded but no jobs, key absent = loading)
const latestJobs = ref<Record<string, StitchJob | null>>({})

const isJobLoaded = (projectId: string) => projectId in latestJobs.value

const loadLatestJobs = async () => {
  await Promise.allSettled(
    projects.value.map(async (project) => {
      try {
        const resp = await listStitchJobs(project.id, { limit: 1, sort: 'startDateDesc' })
        latestJobs.value[project.id] = resp.items[0] ?? null
      } catch {
        latestJobs.value[project.id] = null
      }
    })
  )
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

const loadProjects = async () => {
  isLoading.value = true
  error.value = null
  latestJobs.value = {}
  try {
    const list = await listProjects()
    projects.value = list
    await loadLatestJobs()
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load projects'
  } finally {
    isLoading.value = false
  }
}

const handleCreateProject = async () => {
  if (!newProjectName.value.trim()) return

  isCreating.value = true
  createError.value = null
  try {
    await createProject({
      name: newProjectName.value.trim(),
      description: newProjectDescription.value.trim() || undefined,
    })

    // Clear form
    newProjectName.value = ''
    newProjectDescription.value = ''

    // Reload projects
    await loadProjects()
  } catch (e: any) {
    console.error(e)
    createError.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to create project'
  } finally {
    isCreating.value = false
  }
}

const openWorkspace = (projectId: string) => {
  router.push(`/projects/${projectId}/workspace`)
}

const openHistory = (projectId: string) => {
  router.push(`/projects/${projectId}/history`)
}

const handleDeleteProject = async (projectId: string, projectName: string) => {
  if (!confirm(`Delete project "${projectName}"? This will also delete all photos in this project.`)) {
    return
  }

  try {
    await deleteProject(projectId)
    projects.value = projects.value.filter(p => p.id !== projectId)
  } catch (e: any) {
    console.error(e)
    alert('Failed to delete project: ' + (e?.response?.data?.detail ?? e?.message))
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return date.toLocaleDateString()
}

onMounted(() => {
  loadProjects()
})
</script>
