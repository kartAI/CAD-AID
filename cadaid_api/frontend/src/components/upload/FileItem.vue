<script setup>
import { ref } from 'vue'

defineProps({
  file: {
    type: Object,
    required: true
  },
  progress: {
    type: Number,
    default: 0
  },
  isComplete: {
    type: Boolean,
    default: false
  }
})

const isHovered = ref(false)

// Add mouse event handlers
const onMouseEnter = () => {
  isHovered.value = true
}

const onMouseLeave = () => {
  isHovered.value = false
}
</script>

<template>
  <div class="file-item" @mouseenter="isHovered = true" @mouseleave="isHovered = false">
    <!-- PDF Icon -->
    <svg v-if="file.type === 'application/pdf'" width="36" height="37" viewBox="0 0 36 37" class="file-icon">
      <path d="M21.75 1H5.25C3.875 1 2.75 2.125 2.75 3.5V33.5C2.75 34.875 3.875 36 5.25 36H30.75C32.125 36 33.25 34.875 33.25 33.5V12.5L21.75 1Z" fill="#1E1E1E"/>
      <path d="M21.75 1V12.5H33.25L21.75 1Z" fill="#DDF3EB"/>
    </svg>
    
    <!-- JPEG Icon -->
    <svg v-else width="36" height="27" viewBox="0 0 36 27" class="file-icon">
      <path d="M32.4 0H3.6C1.62 0 0 1.62 0 3.6V23.4C0 25.38 1.62 27 3.6 27H32.4C34.38 27 36 25.38 36 23.4V3.6C36 1.62 34.38 0 32.4 0ZM11.7 15.75L16.2 21.15L22.5 13.05L30.6 23.4H5.4L11.7 15.75Z" fill="#1E1E1E"/>
    </svg>

    <div class="file-info">
      <span class="file-name">{{ file.name }} ({{ progress }}%)</span>
      <div class="progress-bar">
        <div 
          class="progress-fill"
          :style="{ width: `${progress}%` }"
          :class="{ 'completed': isComplete }"
        ></div>
      </div>
    </div>

    <div class="status-icon">
      <div v-if="!isComplete" class="spinner"></div>
      <div v-else class="icon-swap">
        <svg v-if="!isHovered" class="checkmark" width="24" height="24" viewBox="0 0 24 24">
          <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="#3BAF8F"/>
        </svg>
        <button 
          v-else
          class="remove-button"
          @click="$emit('remove', file)"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6L18 18" stroke="#FF4B4B" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-item {
  width: 456px;
  height: 57px;
  background: linear-gradient(135deg, #DDF3EB 0%, #c5e9db 100%);
  border: 1px solid #000000;
  border-radius: 5px;
  display: flex;
  align-items: center;
  padding: 0 15px;
  box-shadow: 4px 4px 8px rgba(46, 45, 48, 0.5);
  margin-bottom: 24px;
  position: relative;
  transition: all 0.3s ease;
  animation: slideIn 0.3s ease-out;
  @mouseenter="onMouseEnter"
  @mouseleave="onMouseLeave"
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.file-item:hover {
  transform: translateX(5px);
  box-shadow: 6px 6px 12px rgba(46, 45, 48, 0.4);
}

.file-icon {
  width: 36px;
}

.file-info {
  flex: 1;
  margin-left: 15px;
}

.file-name {
  display: block;
  font-family: 'Poppins', sans-serif;
  font-size: 12px;
  color: #000000;
  margin-bottom: 3px;
}

.progress-bar {
  width: 338px;
  height: 15px;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3BAF8F 0%, #24BD76 100%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.2) 50%,
    transparent 100%
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #3BAF8F;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.checkmark, .remove-button {
  width: 24px;
  height: 24px;
  transition: opacity 0.2s ease;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-icon {
  width: 24px;
  height: 24px;
  margin-left: 15px;
  position: relative;
}

.icon-swap {
  position: relative;
  width: 24px;
  height: 24px;
}

.remove-button {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.remove-button:hover {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}

.remove-button:hover svg path {
  stroke: #ff3333;
}

/* Add file type indicator */
.file-type {
  position: absolute;
  top: -8px;
  left: 8px;
  background: #3BAF8F;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  text-transform: uppercase;
}

.progress-fill.completed {
  background: linear-gradient(90deg, #3BAF8F 0%, #24BD76 100%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style> 