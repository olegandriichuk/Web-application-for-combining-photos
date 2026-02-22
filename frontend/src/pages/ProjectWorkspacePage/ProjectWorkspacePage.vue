<template>
  <div class="page">
    <!-- Project Header -->
    <div class="project-header">
      <button @click="goBackToProjects" class="back-btn">
        ← Back to Projects
      </button>
      <h1 class="project-title">{{ project?.name || 'Loading...' }}</h1>
      <p v-if="project?.description" class="project-description">
        {{ project.description }}
      </p>
    </div>

    <!-- Uploaded photos OR empty text -->
    <div class="gallery card" v-if="photos.length > 0">
      <div class="card-head">
        <h2 class="card-title">Uploaded Images</h2>
        <p class="card-subtitle">
          {{ photos.length }}
          {{ photos.length === 1 ? 'image ready to stitch' : 'images ready to stitch' }}
        </p>
      </div>

      <div class="photos-scroll">
        <div class="photos-grid">
          <article v-for="(p, idx) in photos" :key="p.id" class="photo-tile">
            <a :href="getPhotoUrl(p.id)" target="_blank" rel="noopener" class="tile-link">
              <img :src="getPhotoUrl(p.id)" :alt="p.original_name" class="tile-img" />
            </a>

            <div class="tile-badge">{{ idx + 1 }}</div>

            <button
              class="tile-close"
              type="button"
              title="Delete"
              @click="onDelete(p.id)"
            >
              ×
            </button>
          </article>
        </div>
      </div>
    </div>

    <div class="card empty-state" v-else>
      <div class="empty-state-text">Upload images to start stitching</div>
    </div>

    <!-- Upload Section -->
    <div class="card">
      <div class="card-head">
        <h2 class="card-title">Upload Your Images</h2>
        <p class="card-subtitle">Select 4–6 images from your device</p>
      </div>

      <label
        class="dropzone"
        :class="{ 'is-disabled': isLoading, 'is-active': isDragActive }"
        @dragenter.prevent="onDragEnter"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
      >
        <input
          class="file-input"
          type="file"
          multiple
          accept="image/*"
          @change="onFilesSelected"
          :disabled="isLoading"
        />

        <div class="dropzone-inner">
          <div class="upload-circle" aria-hidden="true">⤴</div>
          <div class="dz-title">Click to upload image or drag and drop</div>
          <div class="dz-subtitle">Select 4–6 images (JPG, PNG, etc.)</div>

          <div class="dz-meta" v-if="selectedCount > 0">
            Selected: <b>{{ selectedCount }}</b> / 6
          </div>

          <div class="dz-meta dz-warn" v-else>
            No images selected yet
          </div>
        </div>
      </label>

      <div v-if="isLoading" class="status status-loading">Loading...</div>
      <div v-if="error" class="status status-error">{{ error }}</div>
    </div>

    <!-- Stitch Section -->
    <div class="card" v-if="photos.length > 0">
      <div class="card-head">
        <h2 class="card-title">Image Stitching</h2>
        <p class="card-subtitle">Create a stitched image from your uploaded photos</p>
      </div>

      <div class="stitch-toggle">
        <button class="generate-btn" @click="toggleStitchForm">
          <span class="btn-spark" aria-hidden="true">✦</span>
          {{ showStitchForm ? 'Hide Form' : 'Create Stitch Job' }}
        </button>
      </div>
    </div>

    <!-- Stitch Job Form -->
    <StitchJobForm
      v-if="showStitchForm && photos.length > 0"
      :project-id="projectId"
      :photo-ids="photoIds"
      @created="onStitchJobCreated"
    />

    <!-- Stitch Job History -->
    <StitchJobHistory
      v-if="photos.length > 0"
      ref="historyRef"
      :project-id="projectId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  listPhotos as apiListPhotos,
  uploadPhoto as apiUploadPhoto,
  deletePhoto as apiDeletePhoto,
  fetchPhotoBlob,
  type PhotoItem,
} from '../../api/photos'
import { getProject, type Project } from '../../api/projects'
import StitchJobForm from '../../components/StitchJobForm.vue'
import StitchJobHistory from '../../components/StitchJobHistory.vue'
import './ProjectWorkspacePage.css'

const route = useRoute()
const router = useRouter()

const projectId = ref<string>(route.params.id as string)
const project = ref<Project | null>(null)

const photos = ref<PhotoItem[]>([])
const photoBlobUrls = ref<Record<string, string>>({})
const isLoading = ref(false)
const error = ref<string | null>(null)

const selectedCount = ref(0)
const isDragActive = ref(false)
const showStitchForm = ref(false)
const historyRef = ref<InstanceType<typeof StitchJobHistory> | null>(null)

const photoIds = computed(() => photos.value.map(p => p.id))

const getPhotoUrl = (id: string): string => {
  return photoBlobUrls.value[id] || ''
}

const loadProject = async () => {
  try {
    project.value = await getProject(projectId.value)
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load project'
  }
}

const loadPhotoBlobs = async (photoList: PhotoItem[]) => {
  for (const photo of photoList) {
    try {
      photoBlobUrls.value[photo.id] = await fetchPhotoBlob(projectId.value, photo.id)
    } catch (e) {
      console.error(`Failed to load photo ${photo.id}:`, e)
    }
  }
}

const refresh = async () => {
  isLoading.value = true
  error.value = null
  try {
    const list = await apiListPhotos(projectId.value, 100, 0)
    photos.value = [...list].reverse()
    await loadPhotoBlobs(photos.value)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load photos'
  } finally {
    isLoading.value = false
  }
}

onBeforeUnmount(() => {
  Object.values(photoBlobUrls.value).forEach(url => URL.revokeObjectURL(url))
})

const uploadFiles = async (files: File[]) => {
  if (!files.length) return

  const sliced = files.slice(0, 6)
  selectedCount.value = sliced.length

  isLoading.value = true
  error.value = null

  try {
    for (const file of sliced) {
      await apiUploadPhoto(projectId.value, file)
    }
    await refresh()
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Upload failed'
  } finally {
    isLoading.value = false
  }
}


const onFilesSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  await uploadFiles(Array.from(input.files))
  input.value = ''
}

const onDelete = async (id: string) => {
  if (!confirm('Delete this photo?')) return
  isLoading.value = true
  error.value = null
  try {
    await apiDeletePhoto(projectId.value, id)
    photos.value = photos.value.filter((p) => p.id !== id)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to delete'
  } finally {
    isLoading.value = false
  }
}

const onDragEnter = () => { if (!isLoading.value) isDragActive.value = true }
const onDragOver = () => { if (!isLoading.value) isDragActive.value = true }
const onDragLeave = () => { isDragActive.value = false }
const onDrop = async (e: DragEvent) => {
  isDragActive.value = false
  const dt = e.dataTransfer
  if (!dt?.files?.length) return
  await uploadFiles(Array.from(dt.files).filter(f => f.type.startsWith('image/')))
}

const goBackToProjects = () => {
  router.push('/projects')
}

const onStitchJobCreated = () => {
  showStitchForm.value = false
  historyRef.value?.loadJobs()
}

const toggleStitchForm = () => {
  showStitchForm.value = !showStitchForm.value
}

onMounted(async () => {
  await loadProject()
  await refresh()
})
</script>
