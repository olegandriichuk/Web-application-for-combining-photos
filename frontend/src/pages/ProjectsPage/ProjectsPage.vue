<template>
  <div class="page">
    <div class="hero">
      <div class="app-icon" aria-hidden="true">
        <span class="spark">✦</span>
      </div>
      <h1 class="hero-title">Your Projects</h1>
      <p class="hero-subtitle">Organize your image stitching projects</p>
    </div>

    <!-- Create Project Form -->
    <div class="card">
      <div class="card-head">
        <h2 class="card-title">Create New Project</h2>
        <p class="card-subtitle">Start a new image stitching project</p>
      </div>

      <form @submit.prevent="handleCreateProject" class="create-form">
        <div class="form-group">
          <label for="project-name">Project Name *</label>
          <input
            id="project-name"
            v-model="newProjectName"
            type="text"
            placeholder="My Project"
            maxlength="200"
            required
            class="input"
          />
        </div>

        <div class="form-group">
          <label for="project-desc">Description (optional)</label>
          <textarea
            id="project-desc"
            v-model="newProjectDescription"
            placeholder="Brief description of this project"
            maxlength="1000"
            rows="3"
            class="input textarea"
          ></textarea>
        </div>

        <button
          type="submit"
          :disabled="isCreating || !newProjectName.trim()"
          class="btn-primary"
        >
          <span class="btn-spark" aria-hidden="true">+</span>
          Create Project
        </button>
      </form>

      <div v-if="createError" class="status status-error">{{ createError }}</div>
    </div>

    <!-- Projects List -->
    <div class="card" v-if="projects.length > 0">
      <div class="card-head">
        <h2 class="card-title">My Projects</h2>
        <p class="card-subtitle">{{ projects.length }} {{ projects.length === 1 ? 'project' : 'projects' }}</p>
      </div>

      <div class="projects-list">
        <article
          v-for="project in projects"
          :key="project.id"
          class="project-item"
        >
          <div class="project-content">
            <h3 class="project-name">{{ project.name }}</h3>
            <p v-if="project.description" class="project-description">
              {{ project.description }}
            </p>
            <div class="project-meta">
              <span class="meta-item">
                {{ project.photo_count || 0 }} {{ project.photo_count === 1 ? 'image' : 'images' }}
              </span>
              <span class="meta-item">
                Created {{ formatDate(project.created_at) }}
              </span>
            </div>
          </div>

          <div class="project-actions">
            <button
              @click="openProject(project.id)"
              class="btn-secondary"
            >
              Open
            </button>
            <button
              @click="handleDeleteProject(project.id, project.name)"
              class="btn-delete"
              title="Delete project"
            >
              ×
            </button>
          </div>
        </article>
      </div>
    </div>

    <div class="card empty-state" v-else-if="!isLoading">
      <div class="empty-state-text">No projects yet. Create your first project above!</div>
    </div>

    <div v-if="isLoading" class="status status-loading">Loading projects...</div>
    <div v-if="error" class="status status-error">{{ error }}</div>
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
import './ProjectsPage.css'

const router = useRouter()

const projects = ref<Project[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const newProjectName = ref('')
const newProjectDescription = ref('')
const isCreating = ref(false)
const createError = ref<string | null>(null)

const loadProjects = async () => {
  isLoading.value = true
  error.value = null
  try {
    const list = await listProjects()
    projects.value = list
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

const openProject = (projectId: string) => {
  router.push(`/projects/${projectId}`)
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
