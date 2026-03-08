<template>
  <div class="w-[398px] shrink-0 flex flex-col">
    <label
      class="h-[524px] w-full rounded-[14px] border-2 border-[#4954E7] bg-[rgba(73,84,231,0.05)] px-8 py-[81px] flex flex-col items-center justify-center cursor-pointer transition hover:bg-[rgba(73,84,231,0.09)] hover:shadow-[0_14px_30px_rgba(73,84,231,0.12)]"
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
      <div class="flex flex-col items-center gap-[10px] text-center">
        <div class="w-[44px] h-[44px] rounded-full grid place-items-center bg-[rgba(168,85,247,0.12)] text-[#7c3aed] text-[18px]">⤴</div>
        <div class="text-[13px] font-semibold text-[#0f172a]">Click to upload image or drag and drop</div>
        <div class="text-[12px] text-[#64748b]">Select some images (JPG, PNG, etc.)</div>
      </div>
    </label>
    <div v-if="isLoading" class="mt-3 text-[13px] text-[#7c3aed] font-semibold">Loading...</div>
    <div v-if="error" class="mt-3 text-[13px] text-[#ef4444] font-semibold bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] px-3 py-[10px] rounded-xl">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  isLoading: boolean
  error: string | null
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
