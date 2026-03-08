<template>
  <div class="max-w-[1392px] mx-auto mt-[18px] bg-white rounded-[14px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] p-5">

    <!-- Project title + Owner badge -->
    <div class="flex items-start justify-between gap-3 mb-1">
      <h2 class="m-0 text-base font-medium leading-6 text-[#0f172a]">{{ projectName }}</h2>
      <span class="inline-flex items-center py-[0.2rem] px-[0.7rem] bg-[#f3f4f6] text-[#6b7280] border border-[#e5e7eb] rounded-full text-[0.75rem] font-medium whitespace-nowrap shrink-0">Owner</span>
    </div>

    <!-- Project description -->
    <p v-if="projectDescription" class="m-0 text-base font-normal leading-6 text-[#475569] mb-5">{{ projectDescription }}</p>
    <div v-else class="mb-5"></div>

    <!-- Latest job status banner -->
    <div v-if="latestJob" class="flex items-center flex-wrap gap-[10px] px-4 py-3 mb-4 rounded-xl bg-[rgba(248,250,252,0.9)] border border-[rgba(15,23,42,0.08)]">
      <span class="text-[12px] text-[#64748b]">Last submitted job:</span>
      <span class="text-[13px] font-semibold text-[#0f172a]">{{ latestJob.exp_name }}</span>
      <span
        class="py-[2px] px-2 rounded-[20px] text-[11px] font-semibold uppercase tracking-[0.4px]"
        :class="latestJobStatusClass"
      >{{ latestJob.status }}</span>
    </div>

    <!-- Always-visible form -->
    <StitchJobForm
      :project-id="projectId"
      :photo-ids="photoIds"
      :ref-photo-name="refPhotoName"
      @created="onJobCreated"
    />

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type StitchJob } from '@/types/stitchJob'
import StitchJobForm from '@/components/StitchJobForm.vue'

const props = defineProps<{
  projectId: string
  photoIds: string[]
  latestJob: StitchJob | null
  refPhotoName: string | null
  projectName: string
  projectDescription: string
}>()

const emit = defineEmits<{
  'job-created': [job: StitchJob]
}>()

const latestJobStatusClass = computed(() => {
  const map: Record<string, string> = {
    queued:   'bg-[#e2e8f0] text-[#475569]',
    running:  'bg-[#dbeafe] text-[#1d4ed8]',
    finished: 'bg-[#dcfce7] text-[#15803d]',
    failed:   'bg-[#fee2e2] text-[#b91c1c]',
    canceled: 'bg-[#e2e8f0] text-[#475569]',
  }
  return props.latestJob ? (map[props.latestJob.status] ?? '') : ''
})

const onJobCreated = (job: StitchJob) => {
  emit('job-created', job)
}
</script>
