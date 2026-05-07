// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <!-- Loading / error -->
  <div v-if="isLoading" class="py-3 px-4 rounded-md text-sm text-center mb-4 bg-[#eff6ff] text-[#1d4ed8]">Loading projects…</div>
  <div v-if="error" class="py-3 px-4 rounded-md text-sm text-center mb-4 bg-[#fef2f2] text-[#b91c1c]">{{ error }}</div>

  <section class="flex flex-col h-full min-h-0 mb-5 lg:mb-6 xl:mb-8" v-if="!isLoading">
    <h2 class="text-xl font-medium leading-7 tracking-normal text-[#101828] m-0 mb-3 lg:mb-4">Projects</h2>
    
    <!-- Search + Filter bar -->
    <div class="flex gap-2 mb-4 items-center">
      <input
        :value="searchQuery"
        type="text"
        placeholder="Search by name…"
        class="w-[200px] h-9 px-3 rounded-md border border-[#e5e7eb] bg-white text-sm text-[#111827] placeholder-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#bfdbfe] focus:border-[#93c5fd] transition"
        @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        @keydown.enter="emit('search')"
      />
      <button
        @click="emit('search')"
        class="h-9 px-4 rounded-md border border-[#e5e7eb] bg-white text-sm font-medium text-[#111827] hover:bg-[#f9fafb] hover:shadow-md transition cursor-pointer whitespace-nowrap"
      >Search</button>
      <div class="flex-1"></div>
      <button
        @click="emit('open-filters')"
        class="relative h-9 px-3 rounded-md border border-[#e5e7eb] bg-white text-[#6b7280] hover:bg-[#f9fafb] hover:shadow-md transition cursor-pointer flex items-center gap-1.5"
        title="Filters"
      >
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span class="text-sm font-medium">Filter</span>
        <span
          v-if="activeFilterCount > 0"
          class="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-[#4954E7] text-white text-[10px] font-bold flex items-center justify-center"
        >{{ activeFilterCount }}</span>
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="projects.length === 0 && !isLoading && !error"
      class="bg-white rounded-[10px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] text-center text-[#6b7280] py-8 px-6 xl:py-12 text-[0.9375rem]"
    >No projects found.</div>
<div class="flex-1 min-h-0 overflow-y-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
    <div class="flex flex-col gap-3">
      <article
        v-for="project in projects"
        :key="project.id"
        class="relative bg-white rounded-[10px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] overflow-hidden flex items-center"
      >
        <!-- ── PREVIEW THUMBNAIL (square, clickable, only when ref photo loaded) -->
        <button
          v-if="previewUrls[project.id]"
          class="w-[72px] h-[72px] shrink-0 self-center ml-4 rounded-[8px] overflow-hidden border border-[rgba(15,23,42,0.08)] cursor-pointer p-0 bg-transparent hover:opacity-85 transition-opacity"
          title="Open reference photo"
          @click="openPreview(previewUrls[project.id]!)"
        >
          <img
            :src="previewUrls[project.id]"
            class="w-full h-full object-cover"
            alt="Reference photo"
          />
        </button>

        <!-- ── CARD CONTENT ──────────────────────────────────────────── -->
        <div class="flex-1 min-w-0">

        <!-- ── HEADER ────────────────────────────────────────────────── -->
        <div class="flex items-center gap-3 px-5 py-4">

          <!-- Status dot -->
          <template v-if="isJobLoaded(project.id)">
            <span
              :class="statusDotClass(project.id)"
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :title="statusTitle(project.id)"
            ></span>
          </template>
          <span v-else class="w-2.5 h-2.5 rounded-full bg-[#e5e7eb] shrink-0 animate-pulse"></span>

          <!-- Project name + private lock -->
          <div class="flex items-center gap-1.5 min-w-0">
            <h3 class="m-0 text-[15px] font-semibold text-[#111827] truncate">{{ project.name }}</h3>
            <svg v-if="project.is_private" class="shrink-0 text-[#94a3b8]" width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" title="Private">
              <rect x="4" y="8" width="8" height="6" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
              <path d="M6 8V6a2 2 0 1 1 4 0v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>

          <!-- Role badge -->
          <span :class="roleBadgeClass(project.role)" class="shrink-0">{{ project.role.charAt(0).toUpperCase() + project.role.slice(1) }}</span>

          <!-- Last Run -->
          <template v-if="isJobLoaded(project.id)">
            <button
              v-if="latestJobs[project.id]"
              :class="lastRunClass(project.id)"
              class="text-[0.8rem] font-medium underline underline-offset-2 bg-transparent border-none p-0 cursor-pointer whitespace-nowrap shrink-0 hover:opacity-75 transition-opacity"
              @click="openJob(project.id, latestJobs[project.id]!.id)"
            >{{ formatLastRun(latestJobs[project.id]!) }}</button>
            <span v-else class="text-[0.8rem] text-[#9ca3af] whitespace-nowrap shrink-0">No runs yet</span>
          </template>
          <span
            v-else
            class="w-[110px] h-4 rounded-full shrink-0 [background:linear-gradient(90deg,#e5e7eb_25%,#f3f4f6_50%,#e5e7eb_75%)] [background-size:200%_100%] [animation:pp-shimmer_1.4s_infinite]"
          ></span>

          <div class="flex-1"></div>

          <!-- Open button (non-viewer only) -->
          <button
            v-if="project.role !== 'viewer'"
            class="h-[30px] px-4 rounded-md border border-[#e5e7eb] bg-white text-[13px] font-medium text-[#111827] hover:bg-[#f9fafb] hover:shadow-md transition cursor-pointer whitespace-nowrap shrink-0"
            @click="emit('open-workspace', project.id)"
          >Open</button>

          <!-- Actions menu toggle -->
          <div class="shrink-0">
            <button
              :ref="el => setMenuButtonRef(project.id, el)"
              class="h-[30px] px-3 rounded-md border border-[#e5e7eb] bg-white text-[13px] font-medium text-[#6b7280] hover:bg-[#f9fafb] hover:shadow-md transition cursor-pointer flex items-center gap-1"
              @click="toggleMenu(project.id, $event)"
            >
              <svg
                :class="openMenus.has(project.id) ? 'rotate-180' : 'rotate-0'"
                class="transition-transform duration-200"
                width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <!-- Dropdown — teleported to body so overflow:hidden on the card doesn't clip it -->
            <Teleport to="body">
              <Transition name="menu">
                <div
                  v-if="openMenus.has(project.id)"
                  class="fixed w-[190px] bg-white rounded-[10px] border border-[rgba(15,23,42,0.1)] shadow-[0_8px_24px_rgba(15,23,42,0.14)] z-[9999] py-1 overflow-hidden"
                  :style="menuStyle(project.id)"
                  @click.stop
                >
                <!-- Edit -->
                <button
                  v-if="project.role === 'owner'"
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[13px] text-[#374151] hover:bg-[#f9fafb] transition-colors cursor-pointer text-left"
                  @click="handleEdit(project.id)"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13H3v-2L11.5 2.5z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                  </svg>
                  Edit
                </button>

                <!-- Manage users -->
                <button
                  v-if="project.role === 'owner'"
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[13px] text-[#374151] hover:bg-[#f9fafb] transition-colors cursor-pointer text-left"
                  @click="handleManageUsers(project.id)"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="6" cy="5" r="2.5" stroke="currentColor" stroke-width="1.3"/>
                    <path d="M1 13c0-2.761 2.239-4 5-4s5 1.239 5 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                    <path d="M12 7v4m-2-2h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  </svg>
                  Manage users
                </button>

                <!-- View map (tiles ready) -->
                <button
                  v-if="latestFinishedJobs[project.id]?.tiles_ready"
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[13px] text-[#374151] hover:bg-[#f9fafb] transition-colors cursor-pointer text-left"
                  :disabled="openingViewer.has(project.id)"
                  @click="openViewer(project.id, latestFinishedJobs[project.id]!)"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.3"/>
                    <path d="M1.5 8h13M8 1.5C6.5 4 5.5 6 5.5 8s1 4 2.5 6.5M8 1.5C9.5 4 10.5 6 10.5 8s-1 4-2.5 6.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  </svg>
                  {{ openingViewer.has(project.id) ? 'Loading…' : 'View map' }}
                </button>

                <!-- Download -->
                <button
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[13px] transition-colors cursor-pointer text-left"
                  :class="latestFinishedJobs[project.id] ? 'text-[#374151] hover:bg-[#f9fafb]' : 'text-[#9ca3af] cursor-not-allowed'"
                  :disabled="!latestFinishedJobs[project.id] || downloadingIds.has(project.id)"
                  @click="latestFinishedJobs[project.id] && downloadImage(project.id, latestFinishedJobs[project.id]!.id)"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 2v8m-3-3 3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M3 11v1.5A1.5 1.5 0 0 0 4.5 14h7a1.5 1.5 0 0 0 1.5-1.5V11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  </svg>
                  {{ downloadingIds.has(project.id) ? 'Downloading…' : 'Download' }}
                </button>

                <div v-if="project.role === 'owner'" class="my-1 border-t border-[#f3f4f6]"></div>

                <!-- Delete -->
                <button
                  v-if="project.role === 'owner'"
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-[13px] text-[#dc2626] hover:bg-[#fef2f2] transition-colors cursor-pointer text-left"
                  @click="handleDelete(project.id, project.name)"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 4h10M6 4V3h4v1M5 4l.5 8h5L11 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Delete project
                </button>
                </div>
              </Transition>
            </Teleport>
          </div>
        </div>

        <!-- ── BODY ─────────────────────────────────────────────────── -->

        <!-- Collapsed -->
        <div
          v-if="!expandedCards.has(project.id)"
          class="relative px-5 pb-10 pt-0"
        >
          <p class="m-0 text-[13px] text-[#6b7280] leading-[1.55] line-clamp-2">
            {{ project.description || 'No description' }}
          </p>
          <button
            class="absolute bottom-3 right-4 p-1 rounded-md text-[#94a3b8] hover:text-[#4954E7] hover:bg-[#f0f4ff] transition-colors cursor-pointer"
            title="Expand"
            @click="expandedCards = new Set(expandedCards).add(project.id)"
          >
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9.5 2H14v4.5M14 2l-5.5 5.5M6.5 14H2v-4.5M2 14l5.5-5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <!-- Expanded -->
        <div
          v-else
          class="relative px-5 pb-10 pt-0 border-t border-[#f3f4f6]"
        >
          <dl class="mt-3 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5">
            <template v-for="field in metaFields(project)" :key="field.label">
              <dt class="text-[12px] font-semibold text-[#9ca3af] uppercase tracking-wide self-start pt-[1px]">{{ field.label }}</dt>
              <dd class="m-0 text-[13px] text-[#374151]">{{ field.value }}</dd>
            </template>
          </dl>
          <button
            class="absolute bottom-3 right-4 p-1 rounded-md text-[#94a3b8] hover:text-[#4954E7] hover:bg-[#f0f4ff] transition-colors cursor-pointer"
            title="Collapse"
            @click="collapseCard(project.id)"
          >
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 8.5H6.5V13M6.5 8.5 2 14M14 7.5H9.5V3M9.5 7.5 14 2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        </div><!-- end card content -->
      </article>
    </div>
    </div>
  </section>

  <!-- Leaflet Viewer Modal -->
  <LeafletViewer
    v-if="viewer.open"
    :project-id="viewer.projectId"
    :job-id="viewer.jobId"
    :metadata="viewer.metadata!"
    :title="viewer.title"
    :download-url="viewer.downloadUrl"
    @close="viewer.open = false"
  />

  <!-- Photo lightbox -->
  <Teleport to="body">
    <Transition name="lightbox">
      <div
        v-if="lightboxUrl"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-sm"
        @click.self="lightboxUrl = null"
      >
        <div class="relative max-w-[90vw] max-h-[90vh] flex items-center justify-center">
          <img
            :src="lightboxUrl"
            class="max-w-full max-h-[90vh] rounded-[10px] shadow-2xl object-contain"
            alt="Reference photo"
          />
          <button
            class="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors cursor-pointer border-none text-[18px] leading-none"
            @click="lightboxUrl = null"
          >×</button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { type Project } from '@/api/projects'
import { getJobResult, getJobTileMetadata } from '@/api/stitchJobs'
import { fetchPhotoPreviewUrl, listPhotos } from '@/api/photos'
import { type StitchJob, type JobStatus, type TileMetadata } from '@/types/stitchJob'
import LeafletViewer from './LeafletViewer.vue'

const props = defineProps<{
  projects: Project[]
  isLoading: boolean
  error: string | null
  latestJobs: Record<string, StitchJob | null>
  latestFinishedJobs: Record<string, StitchJob | null>
  searchQuery: string
  activeFilterCount: number
}>()

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'search': []
  'open-filters': []
  'open-workspace': [projectId: string]
  'delete-project': [projectId: string, projectName: string]
  'manage-users': [projectId: string]
  'edit-project': [projectId: string]
}>()

const router = useRouter()

// ── Preview image URLs (fetched from latest finished job result) ──────────────

const previewUrls = ref<Record<string, string>>({})

const loadPreviewUrls = async () => {
  await Promise.allSettled(
    Object.entries(props.latestJobs).map(async ([projectId, job]) => {
      if (!job || previewUrls.value[projectId]) return
      try {
        if (job.ref_photo_id) {
          // Fast path: ref_photo_id is set (jobs created after the migration)
          previewUrls.value[projectId] = await fetchPhotoPreviewUrl(projectId, job.ref_photo_id)
        } else if (job.ref_name) {
          // Fallback: old jobs where ref_photo_id was not yet tracked — match by name
          const photos = await listPhotos(projectId)
          const match = photos.find(p => p.original_name === job.ref_name)
          if (match?.preview_url) previewUrls.value[projectId] = match.preview_url
        }
      } catch {}
    })
  )
}

watch(() => props.latestJobs, loadPreviewUrls, { deep: true, immediate: true })

// ── Per-card state ────────────────────────────────────────────────────────────

const expandedCards = ref<Set<string>>(new Set())
const openMenus = ref<Set<string>>(new Set())

// Button element refs + computed fixed positions for the teleported dropdown
const menuButtonRefs = new Map<string, HTMLElement>()
const menuPositions = ref<Record<string, { top: number; right: number }>>({})

const setMenuButtonRef = (id: string, el: unknown) => {
  if (el instanceof HTMLElement) {
    menuButtonRefs.set(id, el)
  } else {
    menuButtonRefs.delete(id)
  }
}

const menuStyle = (id: string): Record<string, string> => {
  const pos = menuPositions.value[id]
  if (!pos) return {}
  return {
    top: `${pos.top}px`,
    right: `${pos.right}px`,
  }
}

const collapseCard = (id: string) => {
  const s = new Set(expandedCards.value)
  s.delete(id)
  expandedCards.value = s
}

const toggleMenu = (id: string, event: MouseEvent) => {
  event.stopPropagation()
  const isOpen = openMenus.value.has(id)
  openMenus.value = new Set()  // close all first
  if (!isOpen) {
    const btn = menuButtonRefs.get(id)
    if (btn) {
      const rect = btn.getBoundingClientRect()
      menuPositions.value[id] = {
        top: rect.bottom + 6,
        right: window.innerWidth - rect.right,
      }
    }
    openMenus.value = new Set([id])
  }
}

// Close all menus when clicking outside
const handleGlobalClick = () => {
  if (openMenus.value.size > 0) openMenus.value = new Set()
}
onMounted(() => document.addEventListener('click', handleGlobalClick))
onBeforeUnmount(() => document.removeEventListener('click', handleGlobalClick))

// ── Helpers ───────────────────────────────────────────────────────────────────

const isJobLoaded = (projectId: string) => projectId in props.latestJobs

const statusDotClass = (projectId: string): string => {
  const status = props.latestJobs[projectId]?.status ?? null
  const map: Record<JobStatus, string> = {
    finished: 'bg-[#16a34a]',
    failed:   'bg-[#dc2626]',
    running:  'bg-[#2563eb] animate-pulse',
    queued:   'bg-[#9ca3af]',
    canceled: 'bg-[#9ca3af]',
  }
  return status ? (map[status] ?? 'bg-[#e5e7eb]') : 'bg-[#e5e7eb]'
}

const statusTitle = (projectId: string): string => {
  const status = props.latestJobs[projectId]?.status
  if (!status) return 'No runs yet'
  return { finished: 'Success', failed: 'Failed', running: 'Running', queued: 'Queued', canceled: 'Canceled' }[status] ?? status
}

const lastRunClass = (projectId: string): string => {
  const status = props.latestJobs[projectId]?.status
  if (status === 'finished') return 'text-[#16a34a]'
  if (status === 'failed') return 'text-[#dc2626]'
  return 'text-[#6b7280]'
}

const formatLastRun = (job: StitchJob): string => {
  const date = new Date(job.started_at ?? job.created_at)
  const d = String(date.getDate()).padStart(2, '0')
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const y = date.getFullYear()
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${d}/${m}/${y}, ${h}:${min}`
}

type MetaField = { label: string; value: string }

const metaFields = (project: Project): MetaField[] => [
  { label: 'Description', value: project.description || '—' },
  { label: 'Region',      value: project.region        || '—' },
  { label: 'Document',    value: project.document_type || '—' },
  { label: 'Collection',  value: project.collection    || '—' },
  { label: 'Institution', value: project.institution   || '—' },
  { label: 'Year',        value: project.year ? String(project.year) : '—' },
]

const roleBadgeClass = (role: string): string => {
  const map: Record<string, string> = {
    owner:  'inline-flex items-center py-[0.15rem] px-[0.6rem] bg-[#f3f4f6] text-[#6b7280] border border-[#e5e7eb] rounded-full text-[0.7rem] font-medium whitespace-nowrap',
    editor: 'inline-flex items-center py-[0.15rem] px-[0.6rem] bg-[#eff6ff] text-[#2563eb] border border-[#bfdbfe] rounded-full text-[0.7rem] font-medium whitespace-nowrap',
    viewer: 'inline-flex items-center py-[0.15rem] px-[0.6rem] bg-[#f0fdf4] text-[#16a34a] border border-[#bbf7d0] rounded-full text-[0.7rem] font-medium whitespace-nowrap',
  }
  return map[role] ?? ''
}

// ── Navigation ────────────────────────────────────────────────────────────────

const openJob = (projectId: string, jobId: string) => {
  router.push(`/projects/${projectId}/history?job=${jobId}`)
}

const lightboxUrl = ref<string | null>(null)

const openPreview = (url: string) => {
  lightboxUrl.value = url
}

// ── Action handlers ───────────────────────────────────────────────────────────

const handleEdit = (projectId: string) => {
  openMenus.value = new Set()
  emit('edit-project', projectId)
}

const handleManageUsers = (projectId: string) => {
  openMenus.value = new Set()
  emit('manage-users', projectId)
}

const handleDelete = (projectId: string, projectName: string) => {
  openMenus.value = new Set()
  emit('delete-project', projectId, projectName)
}

// ── Download ──────────────────────────────────────────────────────────────────

const downloadingIds = ref<Set<string>>(new Set())

const downloadImage = async (projectId: string, jobId: string) => {
  if (downloadingIds.value.has(projectId)) return
  openMenus.value = new Set()
  downloadingIds.value = new Set(downloadingIds.value).add(projectId)
  try {
    const { download_url } = await getJobResult(projectId, jobId)
    window.open(download_url, '_blank')
  } catch (e) {
    console.error('Failed to get download URL:', e)
  } finally {
    const next = new Set(downloadingIds.value)
    next.delete(projectId)
    downloadingIds.value = next
  }
}

// ── LeafletViewer ─────────────────────────────────────────────────────────────

type ViewerState = {
  open: boolean; projectId: string; jobId: string
  metadata: TileMetadata | null; title: string; downloadUrl: string | undefined
}
const viewer = ref<ViewerState>({ open: false, projectId: '', jobId: '', metadata: null, title: '', downloadUrl: undefined })
const openingViewer = ref<Set<string>>(new Set())

const openViewer = async (projectId: string, job: StitchJob) => {
  if (openingViewer.value.has(projectId)) return
  openMenus.value = new Set()
  openingViewer.value = new Set(openingViewer.value).add(projectId)
  try {
    const [metadata, { download_url }] = await Promise.all([
      getJobTileMetadata(projectId, job.id),
      getJobResult(projectId, job.id),
    ])
    viewer.value = { open: true, projectId, jobId: job.id, metadata, title: job.exp_name, downloadUrl: download_url }
  } catch (e) {
    console.error('Failed to open viewer:', e)
  } finally {
    const next = new Set(openingViewer.value)
    next.delete(projectId)
    openingViewer.value = next
  }
}
</script>

<style scoped>
.menu-enter-active,
.menu-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.18s ease;
}
.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}
</style>
