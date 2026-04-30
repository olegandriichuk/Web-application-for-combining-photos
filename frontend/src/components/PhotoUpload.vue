<template>
  <div class="flex flex-col shrink-0 w-[260px]">
  <label
    class="w-full rounded-[14px] border-2 border-[#4954E7] bg-[rgba(73,84,231,0.05)] px-8 py-[81px] flex flex-col items-center justify-center cursor-pointer transition hover:bg-[rgba(73,84,231,0.09)] hover:shadow-[0_14px_30px_rgba(73,84,231,0.12)]"
    :class="{
      'cursor-not-allowed opacity-80': isLoading,
      'bg-[rgba(73,84,231,0.12)] shadow-[0_18px_36px_rgba(73,84,231,0.15)]': isDragActive
    }"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <input
      class="hidden"
      type="file"
      multiple
      accept="image/*"
      @change="onFilesSelected"
      :disabled="isLoading"
    />
    <div v-if="isDeleting" class="flex flex-col gap-[6px] w-full">
      <div class="text-[12px] font-semibold text-[#ef4444] text-center">Deleting…</div>
      <div class="w-full h-[6px] rounded-full bg-[rgba(239,68,68,0.12)] overflow-hidden">
        <div class="h-full rounded-full bg-[#ef4444] animate-pulse" style="width:100%" />
      </div>
    </div>
    <div v-else-if="isLoading" class="flex flex-col gap-[6px] w-full">
      <div class="flex justify-between text-[12px] font-semibold text-[#7c3aed]">
        <span>Uploading…</span>
        <span>{{ uploadProgress }}%</span>
      </div>
      <div class="w-full h-[6px] rounded-full bg-[rgba(73,84,231,0.12)] overflow-hidden">
        <div
          class="h-full rounded-full bg-[#4954E7] transition-all duration-200"
          :style="{ width: `${uploadProgress}%` }"
        />
      </div>
    </div>
    <div v-else class="flex flex-col items-center gap-[10px] text-center">
      <div class="w-[44px] h-[44px] rounded-full grid place-items-center bg-[rgba(168,85,247,0.12)] text-[#7c3aed] text-[18px]">⤴</div>
      <div class="text-[13px] font-semibold text-[#0f172a]">Click to upload image or drag and drop</div>
      <div class="text-[12px] text-[#64748b]">Select some images (JPG, PNG, etc.)</div>
    </div>
  </label>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  isLoading: boolean
  isDeleting: boolean
  uploadProgress: number
}>()

const emit = defineEmits<{
  upload: [files: File[]]
}>()

const isDragActive = ref(false)

const onDragEnter = () => { if (!props.isLoading) isDragActive.value = true }
const onDragOver = () => { if (!props.isLoading) isDragActive.value = true }
const onDragLeave = () => { isDragActive.value = false }

const onDrop = (e: DragEvent) => {
  isDragActive.value = false
  const files = Array.from(e.dataTransfer?.files ?? []).filter(f => f.type.startsWith('image/'))
  if (!files.length) return
  emit('upload', files)
}

const onFilesSelected = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const files = Array.from(input.files)
  emit('upload', files)
  input.value = ''
}
</script>
