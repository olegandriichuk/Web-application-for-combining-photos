<template>
  <div class="flex-1 h-[524px] min-w-0 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
    <div
      v-if="photos.length > 0"
      class="grid gap-[14px]"
      style="grid-template-columns: repeat(auto-fill, 286px);"
    >
      <article
        v-for="(p, idx) in photos"
        :key="p.id"
        class="w-[286px] h-[250px] bg-white rounded-[10px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] p-5 flex flex-col gap-[10px]"
      >
        <!-- Image area -->
        <div class="relative w-[246px] h-[183px] shrink-0 rounded-lg overflow-hidden">
          <a :href="getPhotoUrl(p.id)" target="_blank" rel="noopener" class="block w-full h-full">
            <img
              :src="getPhotoUrl(p.id)"
              :alt="p.original_name"
              class="w-full h-full object-cover"
            />
          </a>
          <!-- Index badge -->
          <div class="absolute top-2 left-2 w-[26px] h-[26px] rounded-full grid place-items-center text-[12px] font-bold text-[#0f172a] bg-white/90 border border-[rgba(15,23,42,0.1)] shadow-[0_2px_6px_rgba(15,23,42,0.12)]">
            {{ idx + 1 }}
          </div>
          <!-- Remove button -->
          <button
            class="absolute top-2 right-2 w-[28px] h-[28px] rounded-full border border-[rgba(15,23,42,0.12)] bg-white/90 shadow-[0_2px_6px_rgba(15,23,42,0.12)] cursor-pointer grid place-items-center text-[18px] leading-none text-[#0f172a] hover:scale-[1.06] transition-transform"
            type="button"
            title="Remove"
            @click="emit('delete', p.id)"
          >×</button>
        </div>

        <!-- File name row with reference selector -->
        <div class="flex items-center gap-2 min-w-0">
          <!-- Reference image radio selector -->
          <button
            type="button"
            title="Set as reference image"
            class="shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors"
            :class="refPhotoId === p.id
              ? 'border-[#4954E7] bg-[#4954E7]'
              : 'border-[#d1d5db] bg-white hover:border-[#4954E7]'"
            @click="emit('select-reference', p.id)"
          >
            <span v-if="refPhotoId === p.id" class="w-2 h-2 rounded-full bg-white block"></span>
          </button>
          <div class="flex flex-col min-w-0 flex-1">
            <p class="m-0 text-sm text-[#111827] font-medium truncate">{{ p.original_name }}</p>
            <p v-if="refPhotoId === p.id" class="m-0 text-[11px] text-[#4954E7] font-semibold">Reference image</p>
          </div>
        </div>

      </article>
    </div>

    <div v-else class="h-full flex items-center justify-center">
      <div class="w-full h-full flex items-center justify-center text-[14px] font-semibold text-[#64748b] px-4 rounded-[14px] border border-dashed border-[rgba(15,23,42,0.14)] bg-[rgba(248,250,252,0.9)]">
        Upload images to start stitching
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type PhotoItem } from '@/api/photos'

defineProps<{
  photos: PhotoItem[]
  getPhotoUrl: (id: string) => string
  refPhotoId: string | null
}>()

const emit = defineEmits<{
  delete: [photoId: string]
  'select-reference': [photoId: string]
}>()
</script>
