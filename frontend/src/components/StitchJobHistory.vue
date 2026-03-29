<template>
  <div class="max-w-90% mx-auto mt-6 flex flex-col flex-1 min-h-0">

    <!-- Filters -->
    <div class="flex items-center gap-2 mb-4 flex-wrap flex-shrink-0">
      <button
        v-for="opt in statusOptions"
        :key="opt.value"
        class="py-[3px] px-[10px] rounded-[20px] text-[11px] font-semibold uppercase tracking-[0.4px] whitespace-nowrap border transition-all cursor-pointer"
        :class="statusFilter === opt.value ? opt.activeClass : 'bg-white text-[#94a3b8] border-[#e5e7eb] hover:border-[#cbd5e1] hover:text-[#64748b]'"
        @click="setFilter(opt.value)"
      >{{ opt.label }}</button>
      <div class="ml-auto">
        <button
          class="h-9 px-4 rounded-md border border-[#e5e7eb] bg-white text-sm font-medium text-[#111827] hover:bg-[#f9fafb] hover:shadow-md transition cursor-pointer whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="isLoading"
          @click="loadJobs"
        >Refresh</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="text-center py-10 text-[#7c3aed] font-semibold text-[14px]">
      Loading jobs...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="p-4 rounded-[10px] bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] text-[#ef4444] text-[13px]">
      {{ error }}
    </div>

    <!-- Empty -->
    <div v-else-if="jobs.length === 0" class="p-[26px] bg-white rounded-[14px] shadow-[0_4px_16px_rgba(0,0,0,0.08)]">
      <div class="text-center text-[14px] font-semibold text-[#64748b] py-7 px-4 rounded-[14px] border border-dashed border-[rgba(15,23,42,0.14)] bg-[rgba(248,250,252,0.9)]">
        No stitch jobs found
      </div>
    </div>

    <!-- Table -->
    <div v-else class="bg-white rounded-[14px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] overflow-hidden flex flex-col flex-1 min-h-0">
      <div class="flex-1 min-h-0 overflow-y-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
        <table class="w-full border-collapse table-fixed">
          <thead>
            <tr class="bg-[#f8fafc] border-b border-[#e2e8f0] sticky top-0 z-10">
              <th class="px-2 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[28px]">#</th>
              <th class="px-2 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[8%]">Experiment Name</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[80px]">Status</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[11%]">Created</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[11%]">Finished</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[5%]">Preset</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[10%]">Reference</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[7%]">Resolution</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[35px]">Format</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[35px]">Scale</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[9%]">Points</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[10%]">Result</th>
              <th class="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-[#64748b] w-[52px]">↓</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(job, idx) in jobs"
              :key="job.id"
              class="group border-b border-[rgba(15,23,42,0.06)] hover:bg-[#f8fafc] transition-colors"
            >
              <td class="px-2 py-2 text-[12px] text-[#94a3b8]">{{ (currentPage - 1) * limit + idx + 1 }}</td>

              <td class="px-2 py-2 text-[12px] font-medium text-[#0f172a]">
                <span class="block truncate" :title="job.exp_name">{{ job.exp_name }}</span>
              </td>

              <td class="px-2 py-2 text-center">
                <span
                  class="py-[2px] px-[6px] rounded-[20px] text-center text-[10px] font-semibold uppercase tracking-[0.4px] whitespace-nowrap"
                  :class="statusClass(job.status)"
                >{{ job.status }}</span>
              </td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569]">{{ formatDate(job.created_at) }}</td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569]">{{ job.finished_at ? formatDate(job.finished_at) : '-' }}</td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569]">
                <span class="block truncate" :title="job.preset_name">{{ job.preset_name }}</span>
              </td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569]">
                <span class="block truncate" :title="job.ref_name">{{ job.ref_name }}</span>
              </td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569] whitespace-nowrap">{{ job.final_res[0] }}×{{ job.final_res[1] }}</td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569] uppercase">{{ job.save_format }}</td>

              <td class="px-2 py-2 text-center text-[11px] text-[#475569]">{{ job.relative_scale }}</td>

              <!-- Corner Points -->
              <td class="px-2 py-2 text-center text-[11px] text-[#475569]">
                <span
                  class="block truncate cursor-default underline decoration-dotted decoration-[#94a3b8] underline-offset-2"
                  @mouseenter="showCornerTooltip($event, job.corner_points)"
                  @mousemove="moveTooltip"
                  @mouseleave="hideTooltip"
                >{{ formatCornersShort(job.corner_points) }}</span>
              </td>

              <!-- Result -->
              <td class="px-2 py-2 text-center">
                <template v-if="job.status === 'finished'">
                  <button
                    v-if="job.tiles_ready"
                    class="py-[2px] px-2 rounded-lg text-center text-[11px] font-semibold bg-[rgba(73,84,231,0.08)] text-[#4954E7] border border-[rgba(73,84,231,0.2)] hover:bg-[rgba(73,84,231,0.14)] transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed whitespace-nowrap"
                    :disabled="openingViewer[job.id]"
                    @click="openViewer(job)"
                  >{{ openingViewer[job.id] ? 'Loading…' : 'View result' }}</button>
                  <span
                    v-else
                    class="text-center text-[11px] text-[#94a3b8] whitespace-nowrap"
                    title="Tile generation in progress"
                  >Generating…</span>
                </template>
                <div v-else-if="job.status === 'failed'" class="flex items-center gap-1 min-w-0">
                  <button
                    class="shrink-0 w-5 h-5 flex items-center justify-center rounded border border-[rgba(185,28,28,0.2)] bg-[rgba(185,28,28,0.05)] text-[#b91c1c] hover:bg-[rgba(185,28,28,0.12)] transition-colors cursor-pointer"
                    :title="copiedId === job.id ? 'Copied!' : 'Copy error message'"
                    @click="copyText(job.id, job.error_message ?? 'Job failed')"
                  >
                    <span v-if="copiedId === job.id" class="text-[9px] font-semibold leading-none">✓</span>
                    <svg v-else width="10" height="10" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M11 5V3.5A1.5 1.5 0 0 0 9.5 2H3.5A1.5 1.5 0 0 0 2 3.5V9.5A1.5 1.5 0 0 0 3.5 11H5" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </button>
                  <span
                    class="text-[11px] text-[#b91c1c] block truncate cursor-default underline decoration-dotted decoration-[#b91c1c] underline-offset-2"
                    @mouseenter="showErrorTooltip($event, job.error_message)"
                    @mousemove="moveTooltip"
                    @mouseleave="hideTooltip"
                  >{{ job.error_message ?? 'Job failed' }}</span>
                </div>
              </td>

              <!-- Download -->
              <td class="px-2 py-2 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button
                    v-if="job.status === 'finished'"
                    class="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-[rgba(16,185,129,0.08)] text-[#065f46] border border-[rgba(16,185,129,0.2)] hover:bg-[rgba(16,185,129,0.14)] transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed text-[14px]"
                    :disabled="loadingResult[job.id]"
                    title="Download result"
                    @click="openDownload(job)"
                  >↓</button>
                  <button
                    v-if="job.status === 'failed' && job.log_s3_key"
                    class="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-[rgba(185,28,28,0.08)] text-[#b91c1c] border border-[rgba(185,28,28,0.2)] hover:bg-[rgba(185,28,28,0.14)] transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed text-[14px]"
                    title="Download logs"
                    @click="openLogDownload(job)"
                  >↓</button>
                  <span v-if="job.status !== 'finished' && !(job.status === 'failed' && job.log_s3_key)" class="text-[12px] text-[#94a3b8]">-</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 mt-5">
      <button
        class="py-2 px-4 border border-[rgba(15,23,42,0.12)] rounded-lg text-[13px] font-medium text-[#0f172a] bg-white cursor-pointer hover:bg-[#f8fafc] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        :disabled="currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      >Previous</button>
      <span class="text-[13px] text-[#64748b]">Page {{ currentPage }} of {{ totalPages }}</span>
      <button
        class="py-2 px-4 border border-[rgba(15,23,42,0.12)] rounded-lg text-[13px] font-medium text-[#0f172a] bg-white cursor-pointer hover:bg-[#f8fafc] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        :disabled="currentPage >= totalPages"
        @click="goToPage(currentPage + 1)"
      >Next</button>
    </div>

  </div>

  <!-- Styled floating tooltip — rendered at body level to escape table clipping -->
  <Teleport to="body">
    <div
      v-if="tooltip.visible"
      class="fixed z-50 pointer-events-none"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px', transform: 'translate(-50%, calc(-100% - 10px))' }"
    >
      <!-- Corner Points tooltip -->
      <div
        v-if="tooltip.type === 'corners'"
        class="bg-white rounded-[10px] border border-[rgba(15,23,42,0.08)] shadow-[0_4px_16px_rgba(15,23,42,0.12)] px-4 py-3 min-w-[180px]"
      >
        <p class="m-0 mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#64748b]">Corner Points</p>
        <div class="flex flex-col gap-[6px]">
          <div
            v-for="(pt, i) in (tooltip.data as [number, number][])"
            :key="i"
            class="flex items-center justify-between gap-4"
          >
            <span class="text-[12px] text-[#94a3b8]">Point {{ i + 1 }}</span>
            <span class="text-[13px] font-medium text-[#0f172a] tabular-nums">({{ pt[0] }}, {{ pt[1] }})</span>
          </div>
        </div>
      </div>

      <!-- Error tooltip -->
      <div
        v-else-if="tooltip.type === 'error'"
        class="bg-white rounded-[10px] border border-[rgba(239,68,68,0.2)] shadow-[0_4px_16px_rgba(15,23,42,0.12)] px-4 py-3 max-w-[480px]"
      >
        <p class="m-0 mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#b91c1c]">Error Details</p>
        <p class="m-0 text-[12px] text-[#0f172a] leading-5 break-words font-mono whitespace-pre-wrap">{{ tooltip.data ?? 'Job failed' }}</p>
      </div>
    </div>
  </Teleport>

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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { listStitchJobs, getJobResult, getJobLog, getJobTileMetadata } from '../api/stitchJobs'
import { type StitchJob, type JobStatus, type TileMetadata } from '../types/stitchJob'
import LeafletViewer from './LeafletViewer.vue'

const props = defineProps<{
  projectId: string
}>()

const jobs = ref<StitchJob[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const statusFilter = ref<JobStatus | ''>('')
const currentPage = ref(1)

const statusOptions = [
  { value: '',         label: 'All',      activeClass: 'bg-[#e2e8f0] text-[#475569] border-[#cbd5e1]' },
  { value: 'queued',   label: 'Queued',   activeClass: 'bg-[#e2e8f0] text-[#475569] border-[#cbd5e1]' },
  { value: 'running',  label: 'Running',  activeClass: 'bg-[#dbeafe] text-[#1d4ed8] border-[#bfdbfe]' },
  { value: 'finished', label: 'Finished', activeClass: 'bg-[#dcfce7] text-[#15803d] border-[#bbf7d0]' },
  { value: 'failed',   label: 'Failed',   activeClass: 'bg-[#fee2e2] text-[#b91c1c] border-[#fecaca]' },
] as const

const setFilter = (value: JobStatus | '') => {
  statusFilter.value = value
  currentPage.value = 1
  loadJobs()
}
const totalPages = ref(1)

// Show more rows on taller screens: ~38px per row, ~260px overhead (header + filters + pagination)
const limit = computed(() => {
  const h = window.innerHeight
  if (h >= 1200) return 20
  if (h >= 900)  return 15
  if (h >= 700)  return 8
  return 8
})

const hasActiveJobs = computed(() =>
  jobs.value.some(j =>
    j.status === 'queued' ||
    j.status === 'running' ||
    (j.status === 'finished' && !j.tiles_ready)
  )
)

let pollInterval: ReturnType<typeof setInterval> | null = null

const startPolling = () => {
  if (!pollInterval) pollInterval = setInterval(loadJobs, 10000)
}
const stopPolling = () => {
  if (pollInterval) { clearInterval(pollInterval); pollInterval = null }
}

watch(hasActiveJobs, (active) => { if (active) startPolling(); else stopPolling() })
onBeforeUnmount(() => stopPolling())

const loadJobs = async () => {
  isLoading.value = true
  error.value = null
  try {
    const params: Record<string, any> = { page: currentPage.value, limit: limit.value, sort: 'startDateDesc' }
    if (statusFilter.value) params.status = statusFilter.value
    const response = await listStitchJobs(props.projectId, params)
    jobs.value = response.items
    totalPages.value = response.pages
  } catch (e: any) {
    console.error('Failed to load stitch jobs:', e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load jobs'
  } finally {
    isLoading.value = false
  }
}


const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadJobs()
  }
}

const statusClass = (status: JobStatus): string => {
  const map: Record<string, string> = {
    queued:   'bg-[#e2e8f0] text-[#475569]',
    running:  'bg-[#dbeafe] text-[#1d4ed8]',
    finished: 'bg-[#dcfce7] text-[#15803d]',
    failed:   'bg-[#fee2e2] text-[#b91c1c]',
  }
  return map[status] ?? ''
}

const formatDate = (dateStr: string): string =>
  new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

const formatCornersShort = (pts: [number, number][]): string => {
  const first = pts[0]
  const last = pts[pts.length - 1]
  if (!first || !last) return '—'
  return `(${first[0]},${first[1]}) … (${last[0]},${last[1]})`
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

type TooltipState = {
  visible: boolean
  x: number
  y: number
  type: 'corners' | 'error' | null
  data: any
}

const tooltip = ref<TooltipState>({ visible: false, x: 0, y: 0, type: null, data: null })

const showCornerTooltip = (e: MouseEvent, pts: [number, number][]) => {
  tooltip.value = { visible: true, x: e.clientX, y: e.clientY, type: 'corners', data: pts }
}

const showErrorTooltip = (e: MouseEvent, message: string | null) => {
  tooltip.value = { visible: true, x: e.clientX, y: e.clientY, type: 'error', data: message }
}

const moveTooltip = (e: MouseEvent) => {
  if (tooltip.value.visible) {
    tooltip.value.x = e.clientX
    tooltip.value.y = e.clientY
  }
}

const hideTooltip = () => {
  tooltip.value.visible = false
}

// ── Copy to clipboard ─────────────────────────────────────────────────────────

const copiedId = ref<string | null>(null)

const copyText = async (jobId: string, text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    copiedId.value = jobId
    setTimeout(() => { copiedId.value = null }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}

// ── Log download ──────────────────────────────────────────────────────────────

const loadingLog = ref<Record<string, boolean>>({})

const openLogDownload = async (job: StitchJob) => {
  if (loadingLog.value[job.id]) return
  loadingLog.value[job.id] = true
  try {
    const { log_url } = await getJobLog(props.projectId, job.id)
    const blob = await fetch(log_url).then(r => r.blob())
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = `${job.exp_name}-${job.id}.txt`
    a.click()
    URL.revokeObjectURL(blobUrl)
  } catch (e) {
    console.error('Failed to get log URL:', e)
  } finally {
    loadingLog.value[job.id] = false
  }
}

// ── Result fetching ───────────────────────────────────────────────────────────

type ResultUrls = { download_url: string }
const resultUrls = ref<Record<string, ResultUrls>>({})
const loadingResult = ref<Record<string, boolean>>({})

const fetchResult = async (job: StitchJob) => {
  if (resultUrls.value[job.id] || loadingResult.value[job.id]) return
  loadingResult.value[job.id] = true
  try {
    resultUrls.value[job.id] = await getJobResult(props.projectId, job.id)
  } catch (e) {
    console.error('Failed to load result URLs for job', job.id, e)
  } finally {
    loadingResult.value[job.id] = false
  }
}

const openDownload = async (job: StitchJob) => {
  await fetchResult(job)
  const urls = resultUrls.value[job.id]
  if (!urls) return
  window.open(urls.download_url, '_blank')
}

// ── Leaflet viewer ────────────────────────────────────────────────────────────

type ViewerState = {
  open: boolean
  projectId: string
  jobId: string
  metadata: TileMetadata | null
  title: string
  downloadUrl: string | undefined
}

const viewer = ref<ViewerState>({
  open: false,
  projectId: '',
  jobId: '',
  metadata: null,
  title: '',
  downloadUrl: undefined,
})

const openingViewer = ref<Record<string, boolean>>({})

const openViewer = async (job: StitchJob) => {
  if (openingViewer.value[job.id]) return
  openingViewer.value[job.id] = true
  try {
    const [metadata] = await Promise.all([
      getJobTileMetadata(props.projectId, job.id),
      fetchResult(job),
    ])
    viewer.value = {
      open: true,
      projectId: props.projectId,
      jobId: job.id,
      metadata,
      title: job.exp_name,
      downloadUrl: resultUrls.value[job.id]?.download_url,
    }
  } catch (e) {
    console.error('Failed to open viewer for job', job.id, e)
  } finally {
    openingViewer.value[job.id] = false
  }
}

watch(() => props.projectId, () => {
  currentPage.value = 1
  loadJobs()
})

onMounted(() => loadJobs())

defineExpose({ loadJobs })
</script>
