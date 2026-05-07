// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-white"
      @click.self="emit('close')"
    >
      <div class="relative w-full h-full flex flex-col">
        <div
          class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3 bg-black/60 backdrop-blur-sm"
        >
          <span class="text-white text-[14px] font-semibold truncate max-w-[60%]">
            {{ title }}
          </span>

          <div class="flex items-center gap-2">
            <button
              v-if="downloadUrl"
              class="py-1.5 px-3 rounded-lg text-[12px] font-semibold bg-white/10 text-white border border-white/20 hover:bg-white/20 transition-colors"
              @click="onDownload"
            >
              Download
            </button>

            <button
              class="w-8 h-8 flex items-center justify-center rounded-lg bg-white/10 text-white border border-white/20 hover:bg-white/20 transition-colors text-[18px] leading-none"
              title="Close"
              @click="emit('close')"
            >
              ×
            </button>
          </div>
        </div>

        <div
          v-if="isLoading"
          class="absolute inset-0 z-10 flex items-center justify-center bg-black/60"
        >
          <div class="text-white text-[14px] font-semibold">Loading tiles...</div>
        </div>

        <div
  ref="mapContainer"
  class="w-full h-full bg-white"
  style="background: white;"
/>
      </div>
    </div>
  </Teleport>
</template>


<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import type { TileMetadata } from '../types/stitchJob'
import { authStore } from '../stores/authStore'
import type { Map as LeafletMap, LatLngBoundsExpression } from 'leaflet'

const TILE_SIZE = 256

const props = defineProps<{
  projectId: string
  jobId: string
  metadata: TileMetadata
  title?: string
  downloadUrl?: string
}>()

const emit = defineEmits<{
  close: []
}>()

const mapContainer = ref<HTMLElement | null>(null)
const isLoading = ref(true)
let map: LeafletMap | null = null

onMounted(async () => {
  if (!mapContainer.value) return

  const L = await import('leaflet')
  await import('leaflet/dist/leaflet.css')

  const token = authStore.getToken()
  const tileUrlTemplate =
    `/api/projects/${props.projectId}/stitch-jobs/${props.jobId}/tiles/{z}/{x}/{y}` +
    (token ? `?token=${encodeURIComponent(token)}` : '')

  const { width, height, min_zoom, max_zoom } = props.metadata

  const tileScale = Math.pow(2, max_zoom)

  // Bounds must be built from the full tile grid, not raw image width/height.
  // Otherwise the rightmost/bottom tile exists but the map clips before reaching it.
  const cols = Math.ceil(width / TILE_SIZE)
  const rows = Math.ceil(height / TILE_SIZE)
  const gridWidth = cols * TILE_SIZE
  const gridHeight = rows * TILE_SIZE

  const coordW = gridWidth / tileScale
  const coordH = gridHeight / tileScale

  const imageBounds: LatLngBoundsExpression = [
    [-coordH, 0],
    [0, coordW],
  ]

  // Small padding so the edge is reachable at max zoom without pulling the map too far off-screen.
  const viewW = mapContainer.value.clientWidth
  const viewH = mapContainer.value.clientHeight
  const padW = viewW / (2 * tileScale)
  const padH = viewH / (2 * tileScale)

  const maxBounds: LatLngBoundsExpression = [
    [-coordH - padH, -padW],
    [padH, coordW + padW],
  ]

  map = L.map(mapContainer.value, {
    crs: L.CRS.Simple,
    minZoom: min_zoom,
    maxZoom: max_zoom,
    maxBounds,
    maxBoundsViscosity: 0.85,
    zoomSnap: 1,
    zoomDelta: 1,
    attributionControl: false,
    zoomControl: false,
  })

  L.control.zoom({ position: 'bottomleft' }).addTo(map)

  L.tileLayer(tileUrlTemplate, {
    tileSize: TILE_SIZE,
    minZoom: min_zoom,
    maxZoom: max_zoom,
    bounds: imageBounds,
    noWrap: true,
    errorTileUrl:
      'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
  }).addTo(map)

  map.fitBounds(imageBounds, {
    padding: [20, 20],
  })

  map.panInsideBounds(maxBounds, { animate: false })

  map.on('load', () => {
    isLoading.value = false
  })

  map.on('tileload', () => {
    isLoading.value = false
  })

  setTimeout(() => {
    isLoading.value = false
  }, 2000)
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})

const onDownload = () => {
  if (props.downloadUrl) window.open(props.downloadUrl, '_blank')
}
</script>