<!-- frontend/src/pages/HomePage.vue -->
<template>
  <div class="page">
    <div class="hero">
      <div class="app-icon" aria-hidden="true">
        <span class="spark">✦</span>
      </div>

      <h1 class="hero-title">Image Blend Generator</h1>
      <p class="hero-subtitle">Upload 4–6 images to create a beautiful blended composition</p>
    </div>

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

      <div class="actions">
        <button
          class="generate-btn"
          @click="refresh"
          :disabled="isLoading || selectedCount < 4"
        >
          <span class="btn-spark" aria-hidden="true">✦</span>
          Generate Blended Image
        </button>

        <p class="hint" v-if="selectedCount < 4">
          Please upload at least 4 images to generate
        </p>
      </div>
    </div>

    <!-- (опційно) превʼю галереї нижче — залишив твою існуючу сітку -->
    <div class="gallery card" v-if="photos.length > 0">
      <div class="card-head">
        <h2 class="card-title">Gallery</h2>
        <p class="card-subtitle">{{ photos.length }} photos</p>
      </div>

      <div class="photos-grid">
        <article v-for="p in photos" :key="p.id" class="photo-card">
          <a :href="photoUrl(p.id)" target="_blank" rel="noopener" class="photo-link">
            <img :src="photoUrl(p.id)" :alt="p.original_name" class="photo-img" />
            <div class="photo-overlay"><span class="view-icon">👁️</span></div>
          </a>

          <div class="photo-meta">
            <div class="photo-name" :title="p.original_name">{{ p.original_name }}</div>
            <div class="photo-info">
              {{ (p.size / 1024).toFixed(1) }} KB • {{ formatDate(p.created_at) }}
            </div>
          </div>

          <div class="photo-actions">
            <a
              :href="photoUrl(p.id)"
              :download="p.original_name"
              class="photo-action-btn download"
              title="Download"
            >⬇️</a>

            <button
              @click="onDelete(p.id)"
              class="photo-action-btn delete"
              title="Delete"
            >🗑️</button>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import './HomePage.css'

import {
  listPhotos as apiListPhotos,
  uploadPhotos as apiUploadPhotos,
  deletePhoto as apiDeletePhoto,
  photoUrl,
  type PhotoItem,
} from '../api/photos'

const photos = ref<PhotoItem[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const selectedCount = ref(0)
const isDragActive = ref(false)

const refresh = async () => {
  isLoading.value = true
  error.value = null
  try {
    photos.value = await apiListPhotos(100, 0)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load photos'
  } finally {
    isLoading.value = false
  }
}

const uploadFiles = async (files: File[]) => {
  if (!files.length) return

  // UI: рахуємо тільки до 6 (як у макеті)
  const sliced = files.slice(0, 6)
  selectedCount.value = sliced.length

  isLoading.value = true
  error.value = null
  try {
    await apiUploadPhotos(sliced)
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
    await apiDeletePhoto(id)
    photos.value = photos.value.filter((p) => p.id !== id)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to delete'
  } finally {
    isLoading.value = false
  }
}

const formatDate = (iso?: string) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

// Drag & drop тільки для стилю/UX (без нових файлів)
const onDragEnter = () => { if (!isLoading.value) isDragActive.value = true }
const onDragOver = () => { if (!isLoading.value) isDragActive.value = true }
const onDragLeave = () => { isDragActive.value = false }
const onDrop = async (e: DragEvent) => {
  isDragActive.value = false
  const dt = e.dataTransfer
  if (!dt?.files?.length) return
  await uploadFiles(Array.from(dt.files).filter(f => f.type.startsWith('image/')))
}

onMounted(() => {
  refresh()
})
</script>
