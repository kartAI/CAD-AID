<script setup>
defineProps({
  progress: {
    type: Number,
    required: true,
    validator: (value) => value >= 0 && value <= 100
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'error'].includes(value)
  }
})
</script>

<template>
  <div class="progress-container">
    <div 
      class="progress-bar" 
      :class="`progress-bar--${variant}`"
      :style="{ width: `${progress}%` }"
    />
  </div>
</template>

<style scoped>
.progress-container {
  width: 100%;
  height: 8px;
  background-color: var(--neutral-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-bar--primary {
  background-color: var(--primary-color);
}

.progress-bar--success {
  background-color: var(--success-color);
}

.progress-bar--error {
  background-color: var(--error-color);
}
</style>
