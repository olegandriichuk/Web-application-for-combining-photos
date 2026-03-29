<template>
  <div class="max-w-[90%] mx-auto py-12 px-4 pb-16 text-[#0f172a]">

    <!-- Project Header -->
    <div class=" mx-auto mb-7">
      <div class="flex items-center justify-between mb-[14px]">
        <button
          @click="goBackToProjects"
          class="px-[14px] py-[6px] bg-white/85 text-[#475569] border border-[rgba(15,23,42,0.12)] rounded-lg text-[13px] font-medium cursor-pointer hover:bg-[#f1f5f9] transition-colors"
        >← </button>
        <div class="flex gap-2 items-center">
          <button
            title="History"
            @click="goToHistory"
            class="w-9 h-9 flex items-center justify-center bg-white border border-[#e5e7eb] rounded-md cursor-pointer text-[#6b7280] shadow-sm hover:shadow-md hover:text-[#111827] transition-shadow p-0"
          >
            <History :size="16" aria-hidden="true" />
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
    </div>

    <!-- Photo grid (left) + Upload panel (right) -->
    <div class=" mx-auto bg-white/[0.92] border border-[rgba(15,23,42,0.06)] rounded-2xl shadow-[0_20px_40px_rgba(15,23,42,0.1),0_1px_0_rgba(255,255,255,0.6)_inset] p-[22px] backdrop-blur-[8px]">
      <div class="mb-3">
        <h2 class="m-0 text-[14px] font-bold text-[#0f172a]">Uploaded Images</h2>
        <p class="mt-[6px] mb-0 text-[12px] text-[#64748b]">
          <template v-if="photos.length > 0">
            {{ photos.length }} {{ photos.length === 1 ? 'image ready to stitch' : 'images ready to stitch' }}
          </template>
          <template v-else>Start by uploading the images you want to stitch together</template>
        </p>
      </div>

      <div class="flex gap-6">
        <UploadedPhotosList
          :photos="photos"
          :get-photo-url="getPhotoUrl"
          :ref-photo-id="refPhotoId"
          @delete="onDelete"
          @select-reference="onSelectReference"
        />
        <PhotoUpload
          :is-loading="isLoading || isDeleting"
          :is-deleting="isDeleting"
          :error="error"
          :upload-progress="uploadProgress"
          @upload="uploadFiles"
        />
      </div>
    </div>

    <!-- Stitch section -->
    <StitchJobParameters
      v-if="photos.length > 0"
      :project-id="projectId"
      :photo-ids="photoIds"
      :latest-job="latestJob"
      :ref-photo-name="refPhotoName"
      :ref-photo-url="refPhotoUrl"
      :ref-photo-original-width="refPhotoOriginalWidth"
      :ref-photo-original-height="refPhotoOriginalHeight"
      :project-name="project?.name ?? ''"
      :project-description="project?.description ?? ''"
      @job-created="onStitchJobCreated"
    />

  </div>

  <ConfirmModal
    v-if="pendingDeletePhotoId"
    title="Delete Photo"
    description="Are you sure you want to remove this photo from the project? This action cannot be undone."
    confirm-label="Delete"
    @confirm="confirmDeletePhoto"
    @cancel="pendingDeletePhotoId = null"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Settings, LogOut, History } from 'lucide-vue-next'
import { authStore } from '@/stores/authStore'
import {
  listPhotos as apiListPhotos,
  uploadPhoto as apiUploadPhoto,
  deletePhoto as apiDeletePhoto,
  type PhotoItem,
} from '../../api/photos'
import { getProject, type Project } from '../../api/projects'
import { type StitchJob } from '../../types/stitchJob'
import { showToast } from '@/lib/toast'
import UploadedPhotosList from '../../components/UploadedPhotosList.vue'
import PhotoUpload from '../../components/PhotoUpload.vue'
import StitchJobParameters from '../../components/StitchJobParameters.vue'
import ConfirmModal from '../../components/ConfirmModal.vue'

const route = useRoute()
const router = useRouter()

const projectId = ref<string>(route.params.projectId as string)
const project = ref<Project | null>(null)

const photos = ref<PhotoItem[]>([])
const isLoading = ref(false)
const isDeleting = ref(false)
const error = ref<string | null>(null)
const uploadProgress = ref(0) // 0–100
const latestJob = ref<StitchJob | null>(null)
const refPhotoId = ref<string | null>(null)

const photoIds = computed(() => photos.value.map(p => p.id))
const refPhotoName = computed(() =>
  photos.value.find(p => p.id === refPhotoId.value)?.original_name ?? null
)
const refPhotoUrl = computed(() =>
  refPhotoId.value ? getPhotoUrl(refPhotoId.value) : null
)
const refPhotoOriginalWidth = computed(() =>
  photos.value.find(p => p.id === refPhotoId.value)?.original_width ?? null
)
const refPhotoOriginalHeight = computed(() =>
  photos.value.find(p => p.id === refPhotoId.value)?.original_height ?? null
)

// Clear reference selection if the selected photo is deleted
watch(photos, (list) => {
  if (refPhotoId.value && !list.find(p => p.id === refPhotoId.value)) {
    refPhotoId.value = null
  }
})

const getPhotoUrl = (id: string): string =>
  photos.value.find(p => p.id === id)?.preview_url ?? ''

const refresh = async () => {
  isLoading.value = true
  error.value = null
  try {
    const list = await apiListPhotos(projectId.value, 100, 0)
    photos.value = [...list].reverse()
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load photos'
  } finally {
    isLoading.value = false
  }
}

const uploadFiles = async (files: File[]) => {
  if (!files.length) return
  isLoading.value = true
  error.value = null
  uploadProgress.value = 0
  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]!
      await apiUploadPhoto(projectId.value, file, (event) => {
        const fileProgress = (event.lengthComputable && event.total) ? event.loaded / event.total : 0
        uploadProgress.value = Math.round((i + fileProgress) / files.length * 100)
      })
      uploadProgress.value = Math.round((i + 1) / files.length * 100)
    }
    await refresh()
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Upload failed'
  } finally {
    isLoading.value = false
    uploadProgress.value = 0
  }
}

const pendingDeletePhotoId = ref<string | null>(null)

const onDelete = (id: string) => {
  pendingDeletePhotoId.value = id
}

const confirmDeletePhoto = async () => {
  const id = pendingDeletePhotoId.value
  pendingDeletePhotoId.value = null
  if (!id) return
  isDeleting.value = true
  error.value = null
  try {
    await apiDeletePhoto(projectId.value, id)
    photos.value = photos.value.filter(p => p.id !== id)
    showToast('Photo removed from project')
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to delete'
  } finally {
    isDeleting.value = false
  }
}

const loadProject = async () => {
  try {
    project.value = await getProject(projectId.value)
    if (project.value.role === 'viewer') {
      router.replace(`/projects/${projectId.value}/history`)
      return
    }
  } catch (e: any) {
    console.error(e)
    error.value = 'Failed to load project'
  }
}

const onSelectReference = (photoId: string) => {
  refPhotoId.value = refPhotoId.value === photoId ? null : photoId
}

const goBackToProjects = () => router.push('/projects')
const goToHistory = () => router.push(`/projects/${projectId.value}/history`)
const handleGoToSettings = () => { router.push('/settings') }
const handleLogout = () => { authStore.logout(); router.push('/login') }

const onStitchJobCreated = (job: StitchJob) => {
  latestJob.value = job
  router.push(`/projects/${projectId.value}/history`)
}

onMounted(async () => {
  await loadProject()
  await refresh()
})
</script>
