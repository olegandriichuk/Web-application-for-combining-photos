<template>
  <div class="max-w-[1392px] mx-auto mt-6">

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <select
        v-model="statusFilter"
        class="py-2 px-3 border border-[rgba(15,23,42,0.12)] rounded-lg text-[13px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] cursor-pointer"
        @change="onFilterChange"
      >
        <option value="">All Statuses</option>
        <option value="queued">Queued</option>
        <option value="running">Running</option>
        <option value="finished">Finished</option>
        <option value="failed">Failed</option>
        <option value="canceled">Canceled</option>
      </select>
      <button
        class="py-2 px-4 border border-[rgba(15,23,42,0.12)] rounded-lg text-[13px] font-medium text-[#0f172a] bg-white cursor-pointer hover:bg-[#f8fafc] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        :disabled="isLoading"
        @click="loadJobs"
      >Refresh</button>
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
    <div v-else class="bg-white rounded-[14px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-[#f8fafc] border-b border-[#e2e8f0]">
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[48px] whitespace-nowrap">#</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] min-w-[150px] whitespace-nowrap">Exp Name</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[110px] whitespace-nowrap">Status</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[155px] whitespace-nowrap">Created</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[155px] whitespace-nowrap">Finished</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[110px] whitespace-nowrap">Preset</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] min-w-[130px] whitespace-nowrap">Reference</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[135px] whitespace-nowrap">Resolution</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[80px] whitespace-nowrap">Format</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[65px] whitespace-nowrap">Scale</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[140px] whitespace-nowrap">Corner Points</th>
              <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748b] min-w-[130px] whitespace-nowrap">Result</th>
              <th class="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-wide text-[#64748b] w-[90px] whitespace-nowrap">Download</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(job, idx) in jobs"
              :key="job.id"
              class="group border-b border-[rgba(15,23,42,0.06)] hover:bg-[#f8fafc] transition-colors"
            >
              <td class="px-4 py-3 text-[13px] text-[#94a3b8]">{{ (currentPage - 1) * limit + idx + 1 }}</td>

              <td class="px-4 py-3 text-[13px] font-medium text-[#0f172a] max-w-[150px]">
                <span class="block truncate" :title="job.exp_name">{{ job.exp_name }}</span>
              </td>

              <td class="px-4 py-3">
                <span
                  class="py-[2px] px-2 rounded-[20px] text-[11px] font-semibold uppercase tracking-[0.4px] whitespace-nowrap"
                  :class="statusClass(job.status)"
                >{{ job.status }}</span>
              </td>

              <td class="px-4 py-3 text-[13px] text-[#475569] whitespace-nowrap">{{ formatDate(job.created_at) }}</td>

              <td class="px-4 py-3 text-[13px] text-[#475569] whitespace-nowrap">{{ job.finished_at ? formatDate(job.finished_at) : '—' }}</td>

              <td class="px-4 py-3 text-[13px] text-[#475569]">{{ job.preset_name }}</td>

              <td class="px-4 py-3 text-[13px] text-[#475569] max-w-[130px]">
                <span class="block truncate" :title="job.ref_name">{{ job.ref_name }}</span>
              </td>

              <td class="px-4 py-3 text-[13px] text-[#475569] whitespace-nowrap">{{ job.final_res[1] }} × {{ job.final_res[0] }}</td>

              <td class="px-4 py-3 text-[13px] text-[#475569] uppercase">{{ job.save_format }}</td>

              <td class="px-4 py-3 text-[13px] text-[#475569]">{{ job.relative_scale }}</td>

              <!-- Corner Points -->
              <td class="px-4 py-3 text-[13px] text-[#475569] max-w-[140px]">
                <span
                  class="block truncate cursor-default underline decoration-dotted decoration-[#94a3b8] underline-offset-2"
                  @mouseenter="showCornerTooltip($event, job.corner_points)"
                  @mousemove="moveTooltip"
                  @mouseleave="hideTooltip"
                >{{ formatCornersShort(job.corner_points) }}</span>
              </td>

              <!-- Result -->
              <td class="px-4 py-3">
                <button
                  v-if="job.status === 'finished'"
                  class="py-1 px-3 rounded-lg text-[12px] font-semibold bg-[rgba(73,84,231,0.08)] text-[#4954E7] border border-[rgba(73,84,231,0.2)] hover:bg-[rgba(73,84,231,0.14)] transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed whitespace-nowrap"
                  disabled
                >View result</button>
                <div v-else-if="job.status === 'failed'" class="flex items-center gap-1 min-w-0">
                  <button
                    class="shrink-0 w-6 h-6 flex items-center justify-center rounded border border-[rgba(185,28,28,0.2)] bg-[rgba(185,28,28,0.05)] text-[#b91c1c] hover:bg-[rgba(185,28,28,0.12)] transition-colors cursor-pointer"
                    :title="copiedId === job.id ? 'Copied!' : 'Copy error message'"
                    @click="copyText(job.id, job.error_message ?? 'Job failed')"
                  >
                    <span v-if="copiedId === job.id" class="text-[10px] font-semibold leading-none">✓</span>
                    <svg v-else width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M11 5V3.5A1.5 1.5 0 0 0 9.5 2H3.5A1.5 1.5 0 0 0 2 3.5V9.5A1.5 1.5 0 0 0 3.5 11H5" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </button>
                  <span
                    class="text-[12px] text-[#b91c1c] block truncate max-w-[130px] cursor-default underline decoration-dotted decoration-[#b91c1c] underline-offset-2"
                    @mouseenter="showErrorTooltip($event, job.error_message)"
                    @mousemove="moveTooltip"
                    @mouseleave="hideTooltip"
                  >{{ job.error_message ?? 'Job failed' }}</span>
                </div>
              </td>

              <!-- Download -->
              <td class="px-4 py-3 text-center">
                <button
                  v-if="job.status === 'finished'"
                  class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-[rgba(16,185,129,0.08)] text-[#065f46] border border-[rgba(16,185,129,0.2)] hover:bg-[rgba(16,185,129,0.14)] transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed text-[16px]"
                  :disabled="loadingResult[job.id]"
                  title="Download result"
                  @click="openDownload(job)"
                >↓</button>
                <span v-else class="text-[13px] text-[#94a3b8]">—</span>
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
        class="bg-white rounded-[10px] border border-[rgba(239,68,68,0.2)] shadow-[0_4px_16px_rgba(15,23,42,0.12)] px-4 py-3 max-w-[320px]"
      >
        <p class="m-0 mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#b91c1c]">Error Details</p>
        <p class="m-0 text-[13px] text-[#0f172a] leading-5 break-words">{{ tooltip.data ?? 'Job failed' }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { listStitchJobs, getJobResult } from '../api/stitchJobs'
import { type StitchJob, type JobStatus } from '../types/stitchJob'

const props = defineProps<{
  projectId: string
}>()

const jobs = ref<StitchJob[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const statusFilter = ref<JobStatus | ''>('')
const currentPage = ref(1)
const totalPages = ref(1)
const limit = 10

const hasActiveJobs = computed(() =>
  jobs.value.some(j => j.status === 'queued' || j.status === 'running')
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
    const params: Record<string, any> = { page: currentPage.value, limit, sort: 'startDateDesc' }
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

const onFilterChange = () => {
  currentPage.value = 1
  loadJobs()
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
    canceled: 'bg-[#e2e8f0] text-[#475569]',
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

// ── Result fetching ───────────────────────────────────────────────────────────

type ResultUrls = { download_url: string; preview_url: string | null }
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

watch(() => props.projectId, () => {
  currentPage.value = 1
  loadJobs()
})

onMounted(() => loadJobs())

defineExpose({ loadJobs })
</script>
