<script setup>
import { ref } from 'vue'
import Button from '../common/Button.vue'

const emit = defineEmits(['filesSelected'])
const fileInput = ref(null)
const isDragging = ref(false)
const files = ref([])

const onDragEnter = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const onDragLeave = (e) => {
  e.preventDefault()
  isDragging.value = false
}

const onDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const droppedFiles = [...e.dataTransfer.files]
  handleFiles(droppedFiles)
}

const onFileInputChange = (e) => {
  const selectedFiles = [...e.target.files]
  handleFiles(selectedFiles)
}

const handleFiles = (selectedFiles) => {
  files.value = selectedFiles
  emit('filesSelected', selectedFiles)
}

const triggerFileInput = () => {
  fileInput.value.click()
}
</script>

<template>
  <div 
    class="file-uploader"
    :class="{ 'is-dragging': isDragging }"
    @dragenter="onDragEnter"
    @dragleave="onDragLeave"
    @dragover.prevent
    @drop="onDrop"
  >
    <input
      ref="fileInput"
      type="file"
      multiple
      class="file-input"
      @change="onFileInputChange"
    >
    
    <div class="upload-content">
      <div class="upload-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 16V8M12 8L9 11M12 8L15 11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M3 15V16C3 18.2091 4.79086 20 7 20H17C19.2091 20 21 18.2091 21 16V15" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      
      <h3 class="upload-title">
        {{ files.length ? `${files.length} files selected` : 'Drop files here' }}
      </h3>
      
      <p class="upload-subtitle">or</p>
      
      <Button 
        variant="primary" 
        size="lg"
        @click="triggerFileInput"
      >
        Browse Files
      </Button>
    </div>
  </div>
</template>

<style scoped>
.file-uploader {
  border: 2px dashed var(--neutral-300);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  text-align: center;
  transition: all 0.2s ease;
  background: var(--neutral-100);
}

.file-uploader.is-dragging {
  border-color: var(--primary-color);
  background: var(--neutral-200);
}

.file-input {
  display: none;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.upload-icon {
  color: var(--primary-color);
  margin-bottom: var(--spacing-sm);
}

.upload-title {
  font-size: var(--font-size-xl);
  color: var(--neutral-700);
  margin: 0;
}

.upload-subtitle {
  color: var(--neutral-500);
  margin: 0;
}
</style>
