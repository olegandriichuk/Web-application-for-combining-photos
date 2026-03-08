<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[9998] flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-[rgba(15,23,42,0.35)] backdrop-blur-[2px]"
        @click="emit('cancel')"
      />
      <!-- Card -->
      <div class="relative bg-white rounded-[14px] shadow-[0_20px_40px_rgba(15,23,42,0.15),0_1px_0_rgba(255,255,255,0.6)_inset] p-6 w-full max-w-[400px]">
        <h2 class="m-0 mb-2 text-[15px] font-semibold text-[#0f172a]">{{ title }}</h2>
        <p class="m-0 mb-6 text-[13px] text-[#475569] leading-5">{{ description }}</p>
        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="px-4 py-2 text-[13px] font-medium text-[#475569] border border-[rgba(15,23,42,0.12)] bg-white rounded-[8px] cursor-pointer hover:bg-[#f1f5f9] transition-colors"
            @click="emit('cancel')"
          >Cancel</button>
          <button
            type="button"
            class="px-4 py-2 text-[13px] font-medium text-white bg-[#ef4444] border-none rounded-[8px] cursor-pointer hover:bg-[#dc2626] transition-colors shadow-[0_2px_8px_rgba(239,68,68,0.3)]"
            @click="emit('confirm')"
          >{{ confirmLabel }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
  confirmLabel: string
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>
