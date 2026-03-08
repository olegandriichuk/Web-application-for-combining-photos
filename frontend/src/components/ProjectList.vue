<template>
  <!-- Loading / global error -->
  <div v-if="isLoading" class="py-3 px-4 rounded-md text-sm text-center mb-4 bg-[#eff6ff] text-[#1d4ed8]">Loading projects…</div>
  <div v-if="error" class="py-3 px-4 rounded-md text-sm text-center mb-4 bg-[#fef2f2] text-[#b91c1c]">{{ error }}</div>

  <!-- Project list -->
  <section class="mb-5 lg:mb-6 xl:mb-8" v-if="!isLoading && projects.length > 0">
    <h2 class="text-xl font-medium leading-7 tracking-normal text-[#101828] m-0 mb-3 lg:mb-4">History</h2>
    <div class="flex flex-col gap-3 xl:gap-4">
      <article
        v-for="project in projects"
        :key="project.id"
        class="bg-white rounded-[10px] p-4 lg:p-5 xl:p-6 shadow-[0_4px_16px_rgba(0,0,0,0.08)] flex flex-col gap-2"
      >
        <!-- Header row: name (left) + Owner pill (top-right) -->
        <div class="flex items-center justify-between gap-3">
          <h3 class="m-0 text-base font-semibold text-[#111827]">{{ project.name }}</h3>
          <span class="inline-flex items-center py-[0.2rem] px-[0.7rem] bg-[#f3f4f6] text-[#6b7280] border border-[#e5e7eb] rounded-full text-[0.75rem] font-medium whitespace-nowrap shrink-0">Owner</span>
        </div>

        <!-- Description -->
        <p class="m-0 text-sm text-[#6b7280] leading-[1.5]">
          {{ project.description || 'No description' }}
        </p>

        <!-- Meta -->
        <div class="flex gap-4 text-[0.8125rem] text-[#9ca3af]">
          <span>{{ project.photo_count || 0 }} {{ project.photo_count === 1 ? 'image' : 'images' }}</span>
          <span>Created {{ formatDate(project.created_at) }}</span>
        </div>

        <!-- Action row: Cancel | Preview | Manage users | Status | Download | Open | Delete -->
        <div class="flex items-center flex-wrap justify-end gap-[10px] mt-2 pt-3 border-t border-[#e5e7eb]">

          <!-- 1. Cancel — only when running -->
          <button
            v-if="latestJobs[project.id]?.status === 'running'"
            class="inline-flex items-center justify-center border rounded-md font-medium cursor-pointer whitespace-nowrap transition py-[0.35rem] px-3 text-[0.8125rem] bg-[#fef2f2] text-[#dc2626] border-[#fecaca] hover:bg-[#fee2e2]"
            @click="emit('cancel-job', project.id, latestJobs[project.id]!.id)"
          >Cancel</button>

          <!-- 2. Preview of the latest image -->
          <button
            class="inline-flex items-center justify-center border rounded-md font-medium whitespace-nowrap py-[0.35rem] px-3 text-[0.8125rem] bg-white text-[#111827] border-[#e5e7eb] opacity-40 cursor-not-allowed pointer-events-none"
            disabled
            title="Coming soon"
          >Preview of latest image</button>

          <!-- 3. Manage users -->
          <button
            class="inline-flex items-center justify-center border rounded-md font-medium whitespace-nowrap py-[0.35rem] px-3 text-[0.8125rem] bg-white text-[#111827] border-[#e5e7eb] opacity-40 cursor-not-allowed pointer-events-none"
            disabled
            title="Coming soon"
          >Manage users</button>

          <!-- 4. Status pill -->
          <template v-if="isJobLoaded(project.id)">
            <button
              :class="[
                'inline-flex items-center justify-center gap-[0.35rem] py-[0.35rem] px-3 rounded-md text-[0.8125rem] font-medium whitespace-nowrap border cursor-pointer hover:brightness-95 transition',
                jobStatusClass(latestJobs[project.id]?.status ?? null)
              ]"
              @click="emit('open-history', project.id)"
              :title="latestJobs[project.id]
                ? `Latest job: ${STATUS_LABELS[latestJobs[project.id]!.status]}`
                : 'No Exposea jobs yet'"
            >
              <span class="w-[7px] h-[7px] rounded-full shrink-0 bg-current" aria-hidden="true"></span>
              {{ latestJobs[project.id] ? STATUS_LABELS[latestJobs[project.id]!.status] : 'No jobs' }}
            </button>
          </template>
          <span
            v-else
            class="inline-block w-[72px] h-[26px] rounded-full [background:linear-gradient(90deg,#e5e7eb_25%,#f3f4f6_50%,#e5e7eb_75%)] [background-size:200%_100%] [animation:pp-shimmer_1.4s_infinite]"
            aria-label="Loading job status"
          ></span>

          <!-- 5. Download image -->
          <button
            v-if="latestFinishedJobs[project.id]"
            class="inline-flex items-center justify-center border rounded-md font-medium whitespace-nowrap transition py-[0.35rem] px-3 text-[0.8125rem] bg-white text-[#111827] border-[#e5e7eb] hover:bg-[#f9fafb] hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            :disabled="downloadingIds.has(project.id)"
            @click="downloadImage(project.id, latestFinishedJobs[project.id]!.id)"
          >{{ downloadingIds.has(project.id) ? 'Downloading…' : 'Download image' }}</button>
          <button
            v-else
            class="inline-flex items-center justify-center border rounded-md font-medium whitespace-nowrap py-[0.35rem] px-3 text-[0.8125rem] bg-white text-[#111827] border-[#e5e7eb] opacity-40 cursor-not-allowed pointer-events-none"
            disabled
            title="No finished job available"
          >Download image</button>

          <!-- 6. Open -->
          <button
            class="inline-flex items-center justify-center border rounded-md font-medium cursor-pointer whitespace-nowrap transition py-[0.35rem] px-3 text-[0.8125rem] bg-white text-[#111827] border-[#e5e7eb] hover:bg-[#f9fafb] hover:shadow-md"
            @click="emit('open-workspace', project.id)"
          >Open</button>

          <!-- 7. Delete — ml-auto pushes it to the right edge, below Owner -->
          <button
            class="inline-flex items-center justify-center border rounded-md font-medium cursor-pointer whitespace-nowrap transition py-[0.35rem] px-3 text-[0.8125rem] bg-[#fef2f2] text-[#dc2626] border-[#fecaca] hover:bg-[#fee2e2]"
            @click="emit('delete-project', project.id, project.name)"
          >Delete project</button>

        </div>
      </article>
    </div>
  </section>

  <!-- Empty state -->
  <div
    class="bg-white rounded-[10px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] text-center text-[#6b7280] py-8 px-6 xl:py-12 text-[0.9375rem]"
    v-else-if="!isLoading && !error"
  >
    No projects yet. Create your first project above!
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { type Project } from '@/api/projects'
import { getJobResult } from '@/api/stitchJobs'
import { STATUS_LABELS, type StitchJob, type JobStatus } from '@/types/stitchJob'

const props = defineProps<{
  projects: Project[]
  isLoading: boolean
  error: string | null
  latestJobs: Record<string, StitchJob | null>
  latestFinishedJobs: Record<string, StitchJob | null>
}>()

const emit = defineEmits<{
  'open-workspace': [projectId: string]
  'open-history': [projectId: string]
  'cancel-job': [projectId: string, jobId: string]
  'delete-project': [projectId: string, projectName: string]
}>()

const isJobLoaded = (projectId: string) => projectId in props.latestJobs

const downloadingIds = ref<Set<string>>(new Set())

const downloadImage = async (projectId: string, jobId: string) => {
  if (downloadingIds.value.has(projectId)) return
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

const jobStatusClass = (status: JobStatus | null): string => {
  const map: Record<string, string> = {
    queued:   'bg-[#f3f4f6] text-[#6b7280] border-[#d1d5db]',
    running:  'bg-[#eff6ff] text-[#2563eb] border-[#bfdbfe]',
    finished: 'bg-[#f0fdf4] text-[#16a34a] border-[#bbf7d0]',
    failed:   'bg-[#fef2f2] text-[#dc2626] border-[#fecaca]',
    canceled: 'bg-[#f3f4f6] text-[#6b7280] border-[#d1d5db]',
  }
  if (!status) return 'bg-[#f9fafb] text-[#9ca3af] border-[#e5e7eb] italic font-normal'
  return map[status] ?? ''
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return date.toLocaleDateString()
}
</script>
