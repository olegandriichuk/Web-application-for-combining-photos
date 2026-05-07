// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

import { ref } from 'vue'

export type Toast = {
  id: number
  message: string
}

const toasts = ref<Toast[]>([])
let nextId = 0

export const showToast = (message: string) => {
  const id = ++nextId
  toasts.value.push({ id, message })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}

export { toasts }
