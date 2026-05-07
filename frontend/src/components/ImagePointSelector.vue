// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <div class="flex flex-col gap-[6px] w-full">
    <div class="flex items-center justify-between">
      <label class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
        Corner Point Selector
        <span class="relative group ml-0.5 inline-flex items-center cursor-default">
          <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
          </svg>
          <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
            <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
            Click on the image to place each of the 4 corner points. Drag any placed point to reposition it. Use scroll wheel or +/– buttons to zoom. Coordinates are automatically filled into the fields below.
          </div>
        </span>
      </label>

      <!-- Zoom controls (outside canvas, top-right) -->
      <div v-if="props.refImageSrc" class="flex items-center gap-1">
        <button
          type="button"
          :disabled="zoom <= MIN_ZOOM"
          class="w-7 h-7 flex items-center justify-center rounded-[6px] bg-white border border-[rgba(15,23,42,0.12)] shadow-sm text-[#64748b] hover:text-[#0f172a] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          title="Zoom out"
          @click.prevent="zoomOut"
        >
          <ZoomOut :size="13" aria-hidden="true" />
        </button>

        <span class="min-w-[38px] text-center text-[11px] font-semibold text-[#0f172a] select-none tabular-nums">
          {{ zoomLabel }}
        </span>

        <button
          type="button"
          :disabled="zoom >= MAX_ZOOM"
          class="w-7 h-7 flex items-center justify-center rounded-[6px] bg-white border border-[rgba(15,23,42,0.12)] shadow-sm text-[#64748b] hover:text-[#0f172a] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          title="Zoom in"
          @click.prevent="zoomIn"
        >
          <ZoomIn :size="13" aria-hidden="true" />
        </button>

        <button
          type="button"
          :disabled="zoom <= 1"
          class="w-7 h-7 flex items-center justify-center rounded-[6px] bg-white border border-[rgba(15,23,42,0.12)] shadow-sm text-[#64748b] hover:text-[#0f172a] transition-all disabled:opacity-40 disabled:cursor-not-allowed ml-0.5"
          title="Reset zoom"
          @click.prevent="resetZoom"
        >
          <RotateCcw :size="13" aria-hidden="true" />
        </button>
      </div>
    </div>

    <div
      class="relative w-full overflow-hidden rounded-[10px] border border-[rgba(15,23,42,0.12)] bg-[rgba(248,250,252,0.9)]"
      style="min-height: 180px;"
    >
      <!-- Locked overlay when no image selected -->
      <div
        v-if="!props.refImageSrc"
        class="absolute inset-0 flex flex-col items-center justify-center gap-2 select-none"
      >
        <svg class="text-[#cbd5e1]" width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <path d="M8 11V7a4 4 0 1 1 8 0v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <p class="m-0 text-[13px] text-[#94a3b8]">Select a reference image to enable point selection</p>
      </div>

      <canvas
        ref="canvasRef"
        class="block w-full"
        :style="{ display: props.refImageSrc ? 'block' : 'none', cursor: cursorStyle }"
        @mousedown.prevent="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseLeave"
        @click="onCanvasClick"
      />

    </div>

    <p class="m-0 text-[11px] text-[#94a3b8]">{{ statusText }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  refImageSrc: string | null
  originalWidth: number | null
  originalHeight: number | null
  currentPoints: [number, number][]
}>()

const emit = defineEmits<{
  (e: 'points-updated', pts: [[number, number], [number, number], [number, number], [number, number]]): void
}>()

// ─── Constants ───────────────────────────────────────────────────────────────

const POINT_COLORS = ['#ef4444', '#f97316', '#22c55e', '#3b82f6']
const POINT_RADIUS = 6
const DRAG_HIT_RADIUS = 8
const MIN_ZOOM = 1
const MAX_ZOOM = 8
const ZOOM_STEP = 0.25
const ZOOM_FACTOR = 1.15

// ─── State ────────────────────────────────────────────────────────────────────

const canvasRef = ref<HTMLCanvasElement | null>(null)
const points = ref<([number, number] | null)[]>([null, null, null, null])
const dragIndex = ref(-1)
const hoverIndex = ref(-1)
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanningRef = ref(false)  // reactive twin of isPanning for cursorStyle

// Non-reactive — avoids Vue wrapping a DOM element or hot-path flags
let loadedImage: HTMLImageElement | null = null
let currentSrc = ''
let resizeObserver: ResizeObserver | null = null
let didDragThisClick = false
let isPanning = false
let panStartX = 0
let panStartY = 0
let panStartPanX = 0
let panStartPanY = 0

// ─── Coordinate helpers ───────────────────────────────────────────────────────

function origWidth(): number {
  return props.originalWidth ?? loadedImage?.naturalWidth ?? 1
}
function origHeight(): number {
  return props.originalHeight ?? loadedImage?.naturalHeight ?? 1
}

// Virtual coords → image coords
function toImageCoords(vx: number, vy: number): [number, number] {
  const canvas = canvasRef.value!
  return [
    Math.round(vx * origWidth() / canvas.width),
    Math.round(vy * origHeight() / canvas.height),
  ]
}

// Image coords → virtual coords
function toDisplayCoords(imgX: number, imgY: number): [number, number] {
  const canvas = canvasRef.value!
  return [
    imgX * canvas.width / origWidth(),
    imgY * canvas.height / origHeight(),
  ]
}

// Raw screen-pixel coords relative to the canvas element
function rawCanvasXY(e: MouseEvent): [number, number] {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  return [
    (e.clientX - rect.left) * scaleX,
    (e.clientY - rect.top) * scaleY,
  ]
}

// Virtual coords = screen coords de-transformed by current zoom/pan
function getCanvasXY(e: MouseEvent): [number, number] {
  const [sx, sy] = rawCanvasXY(e)
  return [
    (sx - panX.value) / zoom.value,
    (sy - panY.value) / zoom.value,
  ]
}

// ─── Pan clamping ─────────────────────────────────────────────────────────────

function clampPan(canvas: HTMLCanvasElement) {
  panX.value = Math.max(canvas.width * (1 - zoom.value), Math.min(0, panX.value))
  panY.value = Math.max(canvas.height * (1 - zoom.value), Math.min(0, panY.value))
}

// ─── Zoom helpers ─────────────────────────────────────────────────────────────

function applyZoom(newZoom: number, focalSX: number, focalSY: number) {
  const canvas = canvasRef.value
  if (!canvas) return
  newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom))
  panX.value = focalSX - (focalSX - panX.value) / zoom.value * newZoom
  panY.value = focalSY - (focalSY - panY.value) / zoom.value * newZoom
  zoom.value = newZoom
  clampPan(canvas)
  redraw()
}

function zoomIn() {
  const c = canvasRef.value
  if (!c) return
  applyZoom(zoom.value + ZOOM_STEP, c.width / 2, c.height / 2)
}

function zoomOut() {
  const c = canvasRef.value
  if (!c) return
  applyZoom(zoom.value - ZOOM_STEP, c.width / 2, c.height / 2)
}

function resetZoom() {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
  redraw()
}

const zoomLabel = computed(() => `${zoom.value.toFixed(1)}×`)

// ─── Drawing ──────────────────────────────────────────────────────────────────

function redraw() {
  const canvas = canvasRef.value
  if (!canvas || !loadedImage) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // Draw image with zoom/pan transform
  ctx.save()
  ctx.translate(panX.value, panY.value)
  ctx.scale(zoom.value, zoom.value)
  ctx.drawImage(loadedImage, 0, 0, canvas.width, canvas.height)
  ctx.restore()

  // Draw markers in screen space (constant visual size regardless of zoom)
  points.value.forEach((pt, i) => {
    if (pt === null) return
    const [vx, vy] = toDisplayCoords(pt[0], pt[1])
    const dx = vx * zoom.value + panX.value
    const dy = vy * zoom.value + panY.value
    const color = POINT_COLORS[i] ?? '#3b82f6'
    const isHovered = hoverIndex.value === i
    const isDragged = dragIndex.value === i
    const r = isDragged ? POINT_RADIUS + 2 : isHovered ? POINT_RADIUS + 1 : POINT_RADIUS

    // Drop shadow
    ctx.shadowColor = 'rgba(0,0,0,0.35)'
    ctx.shadowBlur = 6

    // Fill
    ctx.beginPath()
    ctx.arc(dx, dy, r, 0, Math.PI * 2)
    ctx.fillStyle = color
    ctx.fill()

    ctx.shadowBlur = 0

    // White stroke
    ctx.beginPath()
    ctx.arc(dx, dy, r, 0, Math.PI * 2)
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.stroke()

    // Number label
    ctx.fillStyle = '#ffffff'
    ctx.font = `bold ${r > POINT_RADIUS ? 11 : 10}px Inter, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(String(i + 1), dx, dy)
  })
}

// ─── Canvas sizing ────────────────────────────────────────────────────────────

function syncCanvasSize() {
  const canvas = canvasRef.value
  if (!canvas || !loadedImage) return
  const cssWidth = canvas.clientWidth || (canvas.parentElement?.clientWidth ?? 600)
  canvas.width = cssWidth
  canvas.height = Math.round(cssWidth * loadedImage.naturalHeight / loadedImage.naturalWidth)
  clampPan(canvas)
  redraw()
}

// ─── Image loading ────────────────────────────────────────────────────────────

function loadImage(src: string) {
  currentSrc = src
  const img = new Image()
  img.onload = () => {
    if (src !== currentSrc) return  // stale load
    loadedImage = img
    syncCanvasSize()
  }
  img.onerror = () => {
    if (src !== currentSrc) return
    loadedImage = null
  }
  img.src = src
}

// ─── Watcher ─────────────────────────────────────────────────────────────────

watch(
  () => props.refImageSrc,
  (newSrc) => {
    points.value = [null, null, null, null]
    loadedImage = null
    dragIndex.value = -1
    hoverIndex.value = -1
    zoom.value = 1
    panX.value = 0
    panY.value = 0

    if (newSrc && newSrc.length > 0) {
      loadImage(newSrc)
    } else {
      const canvas = canvasRef.value
      const ctx = canvas?.getContext('2d')
      if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
  },
  { immediate: true }
)

// ─── Sync from external inputs ───────────────────────────────────────────────

watch(
  () => props.currentPoints,
  (newPts) => {
    if (!loadedImage) return
    let changed = false
    newPts.forEach(([x, y], i) => {
      const valid = !isNaN(x) && !isNaN(y) && x >= 0 && y >= 0
      const cur = points.value[i]
      if (valid) {
        if (cur == null || cur[0] !== x || cur[1] !== y) {
          points.value[i] = [x, y]
          changed = true
        }
      } else {
        if (cur !== null) {
          points.value[i] = null
          changed = true
        }
      }
    })
    if (changed) redraw()
  },
  { deep: true }
)

// ─── ResizeObserver ───────────────────────────────────────────────────────────

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  resizeObserver = new ResizeObserver(() => {
    if (loadedImage) syncCanvasSize()
  })
  resizeObserver.observe(canvas)
  // passive: false required — Chrome ignores e.preventDefault() in passive wheel listeners
  canvas.addEventListener('wheel', onWheel, { passive: false })
})

onBeforeUnmount(() => {
  canvasRef.value?.removeEventListener('wheel', onWheel)
  resizeObserver?.disconnect()
  resizeObserver = null
  currentSrc = ''
})

// ─── Hit detection ────────────────────────────────────────────────────────────

// Takes screen-pixel coords so the hit radius stays constant regardless of zoom
function findPointNear(screenX: number, screenY: number): number {
  let closest = -1
  let minDist = DRAG_HIT_RADIUS
  points.value.forEach((pt, i) => {
    if (pt === null) return
    const [vx, vy] = toDisplayCoords(pt[0], pt[1])
    const sx = vx * zoom.value + panX.value
    const sy = vy * zoom.value + panY.value
    const dist = Math.hypot(screenX - sx, screenY - sy)
    if (dist < minDist) {
      minDist = dist
      closest = i
    }
  })
  return closest
}

// ─── Wheel zoom ───────────────────────────────────────────────────────────────

function onWheel(e: WheelEvent) {
  if (!loadedImage || !props.refImageSrc) return
  e.preventDefault()
  const [sx, sy] = rawCanvasXY(e)
  applyZoom(zoom.value * (e.deltaY < 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR), sx, sy)
}

// ─── Event handlers ───────────────────────────────────────────────────────────

function onMouseDown(e: MouseEvent) {
  if (!loadedImage || !props.refImageSrc) return
  const [sx, sy] = rawCanvasXY(e)
  const hit = findPointNear(sx, sy)
  didDragThisClick = hit !== -1
  if (hit !== -1) {
    dragIndex.value = hit
  } else if (zoom.value > 1) {
    isPanning = true
    isPanningRef.value = true
    panStartX = sx
    panStartY = sy
    panStartPanX = panX.value
    panStartPanY = panY.value
  }
}

function onMouseMove(e: MouseEvent) {
  if (!loadedImage || !props.refImageSrc) return

  if (dragIndex.value !== -1) {
    const [vx, vy] = getCanvasXY(e)
    const canvas = canvasRef.value!
    const clampedX = Math.max(0, Math.min(vx, canvas.width))
    const clampedY = Math.max(0, Math.min(vy, canvas.height))
    points.value[dragIndex.value] = toImageCoords(clampedX, clampedY)
    redraw()
    tryEmit()
  } else if (isPanning) {
    const [sx, sy] = rawCanvasXY(e)
    panX.value = panStartPanX + (sx - panStartX)
    panY.value = panStartPanY + (sy - panStartY)
    clampPan(canvasRef.value!)
    redraw()
  } else {
    const [sx, sy] = rawCanvasXY(e)
    const newHover = findPointNear(sx, sy)
    if (newHover !== hoverIndex.value) {
      hoverIndex.value = newHover
      redraw()
    }
  }
}

function onMouseUp() {
  dragIndex.value = -1
  isPanning = false
  isPanningRef.value = false
}

function onMouseLeave() {
  dragIndex.value = -1
  isPanning = false
  isPanningRef.value = false
  if (hoverIndex.value !== -1) {
    hoverIndex.value = -1
    redraw()
  }
}

function onCanvasClick(e: MouseEvent) {
  if (!loadedImage || !props.refImageSrc) return
  if (didDragThisClick) return

  const [sx, sy] = rawCanvasXY(e)
  if (findPointNear(sx, sy) !== -1) return  // near an existing point → ignore

  const emptyIdx = points.value.findIndex(p => p === null)
  if (emptyIdx === -1) return  // all 4 placed; user must drag to adjust

  const [vx, vy] = getCanvasXY(e)
  points.value[emptyIdx] = toImageCoords(vx, vy)
  redraw()
  tryEmit()
}

// ─── Emit ─────────────────────────────────────────────────────────────────────

function tryEmit() {
  if (points.value.every(p => p !== null)) {
    emit('points-updated', points.value as [[number, number], [number, number], [number, number], [number, number]])
  }
}

// ─── Computed ─────────────────────────────────────────────────────────────────

const cursorStyle = computed(() => {
  if (!props.refImageSrc) return 'default'
  if (dragIndex.value !== -1) return 'grabbing'
  if (isPanningRef.value) return 'grabbing'
  if (hoverIndex.value !== -1) return 'grab'
  if (zoom.value > 1) return 'grab'
  return 'crosshair'
})

const statusText = computed(() => {
  if (!props.refImageSrc) return ''
  const placed = points.value.filter(p => p !== null).length
  if (placed === 4) return 'All 4 corner points placed — drag any point to adjust'
  return `Click to place point ${placed + 1} of 4`
})
</script>
