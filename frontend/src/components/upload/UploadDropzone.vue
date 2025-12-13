<template>
  <div
    class="dropzone"
    :class="{ disabled, hasError: !!error }"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <input
      ref="inputRef"
      class="fileInput"
      type="file"
      multiple
      accept="image/*"
      :disabled="disabled"
      @change="onPick"
    />

    <button class="zoneButton" type="button" :disabled="disabled" @click="browse">
      <div class="icon" aria-hidden="true">⤴</div>
      <div class="zoneText">
        <div class="main">Click to upload image or drag and drop</div>
        <div class="sub">Select 4–6 images (JPG, PNG, etc.)</div>
      </div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (e: 'files', files: File[]): void
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const dragActive = ref(false)

const browse = () => inputRef.value?.click()

const onPick = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  emit('files', Array.from(input.files))
  input.value = ''
}

const onDrop = (e: DragEvent) => {
  dragActive.value = false
  if (props.disabled) return
  const files = Array.from(e.dataTransfer?.files ?? []).filter(f => f.type.startsWith('image/'))
  if (files.length) emit('files', files)
}

const onDragOver = () => { if (!props.disabled) dragActive.value = true }
const onDragLeave = () => { dragActive.value = false }
</script>

<style scoped>
.dropzone{
  margin: 0 6px 10px;
  border-radius: 16px;
  border: 1px dashed rgba(148,163,184,.55);
  background: rgba(248, 250, 252, .75);
  padding: 18px;
  transition: border-color .15s, background .15s;
}
.dropzone.hasError{ border-color: rgba(239,68,68,.55); }
.dropzone.disabled{ opacity: .7; }

.fileInput{ display:none; }

.zoneButton{
  width: 100%;
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
  align-items: center;
  border: none;
  background: transparent;
  padding: 18px;
  border-radius: 14px;
  cursor: pointer;
}
.zoneButton:disabled{ cursor: not-allowed; }

.icon{
  width: 44px; height: 44px;
  border-radius: 999px;
  display:grid; place-items:center;
  background: rgba(168,85,247,.12);
  color: #7c3aed;
  font-size: 18px;
}

.zoneText .main{ font-weight: 700; color: #0f172a; font-size: 13px; }
.zoneText .sub{ margin-top: 4px; color:#94a3b8; font-size: 12px; }
</style>
