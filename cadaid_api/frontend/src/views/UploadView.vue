<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/layout/Header.vue'
import Button from '../components/common/Button.vue'
import FileItem from '../components/upload/FileItem.vue'
import apiService from '../services/api.js'

const router = useRouter()
const fileInput = ref(null)
const files = ref([])
const fileProgress = ref({})
const isDragging = ref(false)
const showError = ref(false)
const errorMessage = ref('')
const showSuccess = ref(false)

const hasIncompleteUploads = computed(() => 
  Object.values(fileProgress.value).some(p => p < 100)
)

const handleDragEnter = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  isDragging.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const droppedFiles = [...e.dataTransfer.files]
  handleFiles(droppedFiles)
}

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileInput = (e) => {
  const selectedFiles = [...e.target.files]
  handleFiles(selectedFiles)
}

const handleFiles = async (selectedFiles) => {
  for (const file of selectedFiles) {
    // Add file to files array with initial state
    files.value.push(file)
    fileProgress.value[file.name] = 0
    
    try {
      // Start upload and processing
      const progressInterval = setInterval(() => {
        if (fileProgress.value[file.name] < 90) {
          fileProgress.value[file.name] += 10
        }
      }, 500)

      // Actually upload and process the file
      const result = await apiService.uploadAndProcess([file])
      
      // Complete the progress
      clearInterval(progressInterval)
      fileProgress.value[file.name] = 100
      
      // Update the file's complete status
      const fileIndex = files.value.findIndex(f => f.name === file.name)
      if (fileIndex !== -1) {
        const updatedFile = files.value[fileIndex]
        updatedFile.isComplete = true
        updatedFile.processedData = result
      }
      
      // Show success toast
      showSuccess.value = true
      setTimeout(() => showSuccess.value = false, 3000)
    } catch (error) {
      console.error(`Error processing ${file.name}:`, error)
      errorMessage.value = `Failed to process ${file.name}`
      showError.value = true
    }
  }
}

const handleContinue = () => {
  console.log('Original files:', files.value)
  const processedFiles = files.value.map(file => {
    console.log('Processing file:', file)
    console.log('File processedData:', file.processedData)
    return {
      filename: file.name,
      url: URL.createObjectURL(file),
      detections: file.processedData[0]?.detections || []
    }
  })
  console.log('Processed files before storage:', processedFiles)
  sessionStorage.setItem('uploadedFiles', JSON.stringify(processedFiles))
  router.push('/results')
}

const removeFile = (file) => {
  const index = files.value.findIndex(f => f.name === file.name)
  if (index !== -1) {
    files.value.splice(index, 1)
    delete fileProgress.value[file.name]
  }
}
</script>
<template>
  <main class="upload">
    <div class="back-button-area">
      <Button
        variant="secondary"
        class="back-button"
        @click="router.push('/')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>Tilbake</span>
      </Button>
    </div>
    <Header />
    <div class="container">
      <div class="upload-container">
        <div class="upload-section">
          <h2 class="section-title">Last opp byggesaksdokumenter</h2>
          <div 
            class="file-drop-zone"
            :class="{ 'is-dragging': isDragging }"
            @dragenter="handleDragEnter"
            @dragleave="handleDragLeave"
            @dragover.prevent
            @drop="handleDrop"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              class="file-input"
              @change="handleFileInput"
            >
            <div class="upload-icon">
              <svg width="39" height="34" viewBox="0 0 39 34" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.3333 0.833344L31.8333 13.3333H23.5V25.8333H15.1667V13.3333H6.83334L19.3333 0.833344Z" fill="#1E1E1E"/>
                <path d="M35 29.5V21.1667H31.8333V29.5H6.83334V21.1667H3.66667V29.5C3.66667 31.25 5.08334 32.6667 6.83334 32.6667H31.8333C33.5833 32.6667 35 31.25 35 29.5Z" fill="#1E1E1E"/>
              </svg>
            </div>
            <p class="drop-text">Slipp dine filer her</p>
            <p class="separator">- ELLER -</p>
            <Button 
              class="upload-button"
              variant="primary"
              @click="triggerFileInput"
            >
              Last opp fra maskin
            </Button>
          </div>
        </div>

        <div class="files-section">
          <h2 class="section-title">
            Opplastede filer
            <span v-if="files.length" class="file-count">({{ files.length }})</span>
          </h2>
          <div class="file-list">
            <template v-if="files.length">
              <FileItem
                v-for="file in files"
                :key="file.name"
                :file="file"
                :progress="fileProgress[file.name]"
                :isComplete="file.isComplete"
                @remove="removeFile"
              />
            </template>
            <div v-else class="empty-state">
              <p>Ingen filer er lastet opp</p>
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <path d="M24 4L36 16H28V28H20V16H12L24 4Z" fill="#DDF3EB"/>
                <path d="M40 32V24H36V32H12V24H8V32C8 34 10 36 12 36H36C38 36 40 34 40 32Z" fill="#DDF3EB"/>
              </svg>
            </div>
          </div>
          <Button 
            v-if="files.length"
            class="continue-button"
            variant="primary"
            :disabled="hasIncompleteUploads"
            @click="handleContinue"
          >
            Fortsett til resultater
          </Button>
        </div>
      </div>
    </div>
    <!-- Add success toast -->
    <div v-if="showSuccess" class="success-toast">
      Fil lastet opp!
    </div>
  </main>
</template>

<style scoped>
.upload {
  min-height: 100vh;
  background: linear-gradient(135deg, #DDF3EB 0%, #c5e9db 100%);
  padding-top: 115px;
}

.upload-container {
  width: 1142px;
  height: 480px;
  background: #FFFFFF;
  border-radius: 5px;
  margin: 214.5px auto 0;
  padding: 23px 40px;
  box-shadow: 4px 4px 20px rgba(46, 45, 48, 0.5),
              0 0 30px rgba(36, 189, 118, 0.1);
  display: flex;
  justify-content: space-between;
  animation: fadeIn 0.5s ease-out;
  transition: transform 0.3s ease;
}

.upload-container:hover {
  transform: scale(1.005);
}

.upload-container .upload-section, .upload-container .files-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.section-title {
  font-family: 'Poppins', sans-serif;
  font-weight: 400;
  font-size: 24px;
  color: #000000;
  margin-bottom: 54px;
  text-align: center;
}

.file-drop-zone {
  width: 488px;
  height: 296px;
  background: #DDF3EB;
  border: 1px dashed #000000;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 19px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.file-drop-zone::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, rgba(36, 189, 118, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.file-drop-zone:hover::before {
  opacity: 1;
}

.file-drop-zone.is-dragging {
  background: #c5e9db;
  transform: scale(1.01);
  border-color: #24BD76;
  box-shadow: 0 0 15px rgba(36, 189, 118, 0.2);
}

.file-input {
  display: none;
}

.drop-text {
  font-family: 'Poppins', sans-serif;
  font-weight: 300;
  font-size: 24px;
  color: #000000;
}

.separator {
  font-family: 'Poppins', sans-serif;
  font-weight: 300;
  font-size: 24px;
  color: #000000;
}

.upload-button {
  width: 265.3px;
  height: 52.74px;
  background: #24BD76;
  border-radius: 10px;
  font-family: 'Noto Sans Display', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #2E2D30;
}

.files-section {
  width: 480px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-list {
  flex: 1;
  max-height: 296px;
  overflow-y: auto;
  margin-bottom: 20px;
  padding-right: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
}

.continue-button {
  width: 265.3px;
  height: 52.74px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Noto Sans Display', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #2E2D30;
}

.continue-button:not(:disabled) {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(36, 189, 118, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(36, 189, 118, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(36, 189, 118, 0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Custom scrollbar styling */
.file-list::-webkit-scrollbar {
  width: 8px;
}

.file-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.file-list::-webkit-scrollbar-thumb {
  background: #24BD76;
  border-radius: 4px;
}

.file-list::-webkit-scrollbar-thumb:hover {
  background: #1ea365;
}

/* Adjust file item margin to account for new padding */
.file-item:last-child {
  margin-bottom: 0;
}

.upload-icon {
  transition: transform 0.3s ease;
}

.file-drop-zone:hover .upload-icon {
  transform: translateY(-3px);
}

.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%);
  color: white;
  padding: 15px 25px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(255, 75, 75, 0.2);
  z-index: 1000;
  animation: slideInAndShake 0.5s ease-out;
}

@keyframes slideInAndShake {
  0% { transform: translateX(100%); }
  60% { transform: translateX(-10px); }
  80% { transform: translateX(5px); }
  100% { transform: translateX(0); }
}

.back-button-area {
  position: fixed;
  left: -160px;
  top: 50%;
  transform: translateY(-50%);
  padding: 20px;
  z-index: 100;
  transition: all 0.3s ease;
}

.back-button-area:hover {
  left: 20px;
}

.back-button {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  background: linear-gradient(135deg, #3BAF8F 0%, #24BD76 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 0 8px 8px 0;
  box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  min-width: 180px;
}

.back-button svg {
  width: 24px;
  height: 24px;
  vertical-align: middle;
}

.back-button span {
  font-family: 'Poppins', sans-serif;
  font-size: 16px;
  line-height: 1; /* Reset line-height to center text */
  padding-top: 10px; /* Adjust to fine-tune vertical alignment */
  margin-left: 10px; /* Extra space between icon and text */
}

.file-count {
  font-size: 18px;
  color: #3BAF8F;
  margin-left: 8px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  gap: 12px;
}

.continue-button:disabled {
  background: #cccccc;
  cursor: not-allowed;
  animation: none;
  opacity: 0.7;
}

/* Add loading indicator when uploads are in progress */
.continue-button:disabled::after {
  content: '(Vennligst vent)';
  margin-left: 8px;
  font-size: 14px;
  opacity: 0.8;
}

.success-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #3BAF8F 0%, #24BD76 100%);
  color: white;
  padding: 15px 25px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(36, 189, 118, 0.2);
  z-index: 1000;
  animation: slideInAndShake 0.5s ease-out;
}
</style>

