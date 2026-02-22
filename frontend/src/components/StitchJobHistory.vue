<template>
  <div class="history-card">
    <div class="card-head">
      <h2 class="card-title">Stitch Job History</h2>
      <p class="card-subtitle">View and track your stitching jobs</p>
    </div>

    <!-- Filters -->
    <div class="filters">
      <select v-model="statusFilter" class="filter-select" @change="loadJobs">
        <option value="">All Statuses</option>
        <option value="queued">Queued</option>
        <option value="running">Running</option>
        <option value="finished">Finished</option>
        <option value="failed">Failed</option>
        <option value="canceled">Canceled</option>
      </select>
      <button class="refresh-btn" @click="loadJobs" :disabled="isLoading">
        Refresh
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      Loading jobs...
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      {{ error }}
    </div>

    <!-- Empty State -->
    <div v-else-if="jobs.length === 0" class="empty-state">
      <div class="empty-state-text">No stitch jobs found</div>
    </div>

    <!-- Jobs List -->
    <div v-else class="jobs-list">
      <div v-for="job in jobs" :key="job.id" class="job-card">
        <div class="job-header">
          <span class="job-name">{{ job.exp_name }}</span>
          <span class="job-status" :style="{ backgroundColor: STATUS_COLORS[job.status] }">
            {{ STATUS_LABELS[job.status] }}
          </span>
        </div>

        <div class="job-details">
          <div class="detail-row">
            <span class="detail-label">Reference:</span>
            <span class="detail-value">{{ job.ref_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Preset:</span>
            <span class="detail-value">{{ job.preset_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Resolution:</span>
            <span class="detail-value">{{ job.final_res[0] }} x {{ job.final_res[1] }} px</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Format:</span>
            <span class="detail-value">{{ job.save_format.toUpperCase() }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Scale:</span>
            <span class="detail-value">{{ job.relative_scale }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Photos:</span>
            <span class="detail-value">{{ job.photo_ids.length }} image(s)</span>
          </div>
        </div>

        <div class="job-timestamps">
          <div class="timestamp">
            <span class="timestamp-label">Created:</span>
            <span class="timestamp-value">{{ formatDate(job.created_at) }}</span>
          </div>
          <div v-if="job.started_at" class="timestamp">
            <span class="timestamp-label">Started:</span>
            <span class="timestamp-value">{{ formatDate(job.started_at) }}</span>
          </div>
          <div v-if="job.finished_at" class="timestamp">
            <span class="timestamp-label">Finished:</span>
            <span class="timestamp-value">{{ formatDate(job.finished_at) }}</span>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="job.error_message" class="job-error">
          {{ job.error_message }}
        </div>

        <!-- Actions -->
        <div class="job-actions">
          <a
            v-if="job.result_s3_key && job.status === 'finished'"
            :href="getResultUrl(job.result_s3_key)"
            target="_blank"
            class="action-btn view-btn"
          >
            View Result
          </a>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        class="page-btn"
        :disabled="currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      >
        Previous
      </button>
      <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
      <button
        class="page-btn"
        :disabled="currentPage >= totalPages"
        @click="goToPage(currentPage + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { listStitchJobs } from '../api/stitchJobs'
import {
  STATUS_LABELS,
  STATUS_COLORS,
  type StitchJob,
  type JobStatus,
} from '../types/stitchJob'

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

const loadJobs = async () => {
  isLoading.value = true
  error.value = null

  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      limit,
      sort: 'startDateDesc',
    }

    if (statusFilter.value) {
      params.status = statusFilter.value
    }

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

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString()
}

const getResultUrl = (s3Key: string): string => {
  // This would be a presigned URL or public URL from the backend
  // For now, return a placeholder
  return `/api/results/${s3Key}`
}

watch(() => props.projectId, () => {
  currentPage.value = 1
  loadJobs()
})

onMounted(() => {
  loadJobs()
})

defineExpose({ loadJobs })
</script>

<style scoped>
.history-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.1), 0 1px 0 rgba(255, 255, 255, 0.6) inset;
  padding: 22px;
  backdrop-filter: blur(8px);
  max-width: 980px;
  margin: 0 auto;
}

.card-head {
  margin-bottom: 16px;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.card-subtitle {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 8px;
  font-size: 13px;
  color: #0f172a;
  background: rgba(248, 250, 252, 0.9);
  cursor: pointer;
}

.refresh-btn {
  padding: 8px 16px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
  background: #fff;
  cursor: pointer;
  transition: background 0.15s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: #f8fafc;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #7c3aed;
  font-weight: 600;
  font-size: 14px;
}

.error-state {
  padding: 16px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
  font-size: 13px;
}

.empty-state {
  padding: 26px;
}

.empty-state-text {
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  padding: 28px 16px;
  border-radius: 14px;
  border: 1px dashed rgba(15, 23, 42, 0.14);
  background: rgba(248, 250, 252, 0.9);
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.job-card {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(248, 250, 252, 0.7);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.job-name {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.job-status {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.job-details {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.detail-row {
  display: flex;
  gap: 8px;
}

.detail-label {
  font-size: 12px;
  color: #64748b;
}

.detail-value {
  font-size: 12px;
  font-weight: 500;
  color: #0f172a;
}

.job-timestamps {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.timestamp {
  display: flex;
  gap: 6px;
}

.timestamp-label {
  font-size: 11px;
  color: #94a3b8;
}

.timestamp-value {
  font-size: 11px;
  color: #64748b;
}

.job-error {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  color: #ef4444;
  font-size: 12px;
}

.job-actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.view-btn {
  background: rgba(59, 130, 246, 0.1);
  color: #1e40af;
  border: 1px solid rgba(59, 130, 246, 0.18);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
  background: #fff;
  cursor: pointer;
  transition: background 0.15s ease;
}

.page-btn:hover:not(:disabled) {
  background: #f8fafc;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #64748b;
}
</style>
