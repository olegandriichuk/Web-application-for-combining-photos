<template>
  <div class="page">
    <!-- Header -->
    <div class="project-header">
      <button @click="goBackToProjects" class="back-btn">← Back to Projects</button>
      <h1 class="project-title">
        {{ project?.name || 'Loading...' }} — Job History
      </h1>
      <p v-if="project?.description" class="project-subtitle">{{ project.description }}</p>
    </div>

    <div v-if="projectError" class="status status-error">{{ projectError }}</div>

    <!-- History component -->
    <StitchJobHistory :project-id="projectId" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, type Project } from '../../api/projects'
import StitchJobHistory from '../../components/StitchJobHistory.vue'
import './ProjectHistoryPage.css'

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

const goBackToProjects = () => {
  router.push('/projects')
}

onMounted(() => {
  loadProject()
})
</script>
