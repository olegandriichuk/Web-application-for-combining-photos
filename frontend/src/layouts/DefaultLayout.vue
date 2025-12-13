<template>
  <div class="layout">
    <main class="container">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  background: radial-gradient(circle at 20% 10%, rgba(236, 72, 153, 0.08), transparent 45%),
              radial-gradient(circle at 80% 30%, rgba(168, 85, 247, 0.10), transparent 55%),
              linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 28px 16px 56px;
  display: flex;
  justify-content: center;
}

.container {
  width: min(1020px, 100%);
}
</style>
