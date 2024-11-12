<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Header from '../components/layout/Header.vue'
import Button from '../components/common/Button.vue'
import FileViewer from '../components/common/FileViewer.vue'
import apiService from '../services/api.js'

const router = useRouter()
const route = useRoute()
const results = ref([])
const activeFileIndex = ref(0)
const showFeedback = ref(false)
const feedback = ref({ correct: null })
const toggleStates = ref({
  documents: false,
  rooms: false,
  otherInfo: false,
  documentFeedback: false,
  roomFeedback: false,
  otherInfoFeedback: false
})
const highlightedArea = ref(null)

const currentFile = computed(() => results.value[activeFileIndex.value])

const documentCount = computed(() => {
  return currentFile.value?.processedData?.detections?.length || 0
})

const roomCount = computed(() => {
  return currentFile.value?.processedData?.room_names?.length || 0
})

onMounted(() => {
  try {
    const uploadedFiles = sessionStorage.getItem('uploadedFiles')
    console.log('Retrieved files:', uploadedFiles)
    
    if (!uploadedFiles) {
      router.push('/upload')
      return
    }

    const parsedFiles = JSON.parse(uploadedFiles)
    console.log('Parsed files:', parsedFiles)
    
    if (!parsedFiles || !parsedFiles.length) {
      console.log('No valid files')
      router.push('/upload')
      return
    }

    results.value = parsedFiles.map(file => ({
      filename: file.filename,
      url: file.url,
      processedData: {
        detections: file.detections || [],
        drawing_types: file.detections?.map(d => d.drawing_type) || [],
        room_names: file.detections?.flatMap(d => d.room_names || []) || [],
        cardinal_direction: file.detections?.[0]?.cardinal_direction,
        scale: file.detections?.[0]?.scale,
        gnr_bnr: file.detections?.[0]?.gnr_bnr
      }
    }))
    console.log('Set results:', results.value)
  } catch (error) {
    console.error('Error:', error)
    router.push('/upload')
  }
})

const handleFileChange = (index) => {
  activeFileIndex.value = index
}

const handleFeedback = async (feedback) => {
  try {
    let fieldType, fieldValue
    
    // Determine field type and value based on feedback object
    if (feedback.type) {
      fieldType = 'drawing_type'
      fieldValue = feedback.type
    } else if (feedback.room) {
      fieldType = 'room_name'
      fieldValue = feedback.room
    } else if (feedback.field) {
      fieldType = feedback.field
      fieldValue = feedback.value
    }

    await apiService.submitFeedback({
      filename: currentFile.value.filename,
      field_type: fieldType,
      field_value: fieldValue,
      user_response: feedback.isCorrect
    })

    // Show success message
    showFeedback.value = true
    feedback.value = { correct: feedback.isCorrect }
    
    // Hide success message after 3 seconds
    setTimeout(() => {
      showFeedback.value = false
      feedback.value = { correct: null }
    }, 3000)
  } catch (error) {
    console.error('Failed to submit feedback:', error)
  }
}

const analyzeMore = () => {
  router.push('/upload')
}

const numberToText = (num) => {
  const numbers = ['null', 'en', 'to', 'tre', 'fire', 'fem', 'seks', 'syv', 'åtte', 'ni', 'ti']
  return numbers[num] || num.toString()
}

const previousFile = () => {
  if (activeFileIndex.value > 0) {
    activeFileIndex.value--
  }
}

const nextFile = () => {
  if (activeFileIndex.value < results.value.length - 1) {
    activeFileIndex.value++
  }
}

const isFloorPlan = computed(() => {
  return currentFile.value?.processedData?.drawing_types?.some(
    type => type.toLowerCase() === 'plantegning'
  )
})

const highlightBBox = (item) => {
  // Find the detection that matches this drawing type
  if (typeof item === 'string') {
    const detection = currentFile.value?.processedData?.detections?.find(
      d => d.drawing_type?.toLowerCase() === item.toLowerCase()
    )
    if (detection) {
      highlightedArea.value = {
        bbox: detection.bbox,
        label: detection.drawing_type
      }
    }
  } else {
    highlightedArea.value = {
      bbox: item.bbox,
      label: item.drawing_type || item
    }
  }
}

const clearHighlight = () => {
  highlightedArea.value = null
}
</script>

<template>
  <main class="results">
    <Header />
    <div class="container">
      <!-- Left side - Document viewer -->
      <div class="document-viewer">
        <h2 class="file-title">{{ currentFile?.filename }}</h2>
        <div class="viewer-content">
          <FileViewer 
            :file="currentFile"
            :highlightedArea="highlightedArea"
          />
        </div>
        <div class="file-picker">
          <button class="arrow-button left" @click="previousFile">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M20 8L12 16L20 24" stroke="#87A7A1" stroke-width="2"/>
            </svg>
          </button>
          
          <div class="thumbnail-container">
            <div 
              v-for="(file, index) in results" 
              :key="file.filename"
              class="thumbnail"
              :class="{ active: index === activeFileIndex }"
              @click="handleFileChange(index)"
            >
              <img :src="file.url" :alt="file.filename">
            </div>
          </div>
          
          <button class="arrow-button right" @click="nextFile">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M12 8L20 16L12 24" stroke="#87A7A1" stroke-width="2"/>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Right side - Results and Feedback -->
      <div class="right-panel">
        <div class="results-panel">
          <h2 class="panel-title">Resultater fra Modell</h2>
          
          <!-- Documents Section -->
          <div class="result-section">
            <button class="toggle-button" @click="toggleStates.documents = !toggleStates.documents">
              <svg :class="{ rotated: toggleStates.documents }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">
                Jeg fant <span class="highlight">{{ numberToText(documentCount) }}</span> dokumenter
              </span>
            </button>
            
            <div v-if="toggleStates.documents" class="section-content">
              <p class="result-text">
                <span v-for="(detection, index) in currentFile?.processedData?.detections" :key="index">
                  <span class="field-name">"{{ detection.drawing_type }}"</span>
                  <span v-if="index < currentFile?.processedData?.detections.length - 1" class="conjunction"> og </span>
                </span>
              </p>
            </div>
          </div>

          <!-- Rooms Section (only show if drawing_type includes 'plantegning') -->
          <div v-if="isFloorPlan" class="result-section">
            <button class="toggle-button" @click="toggleStates.rooms = !toggleStates.rooms">
              <svg :class="{ rotated: toggleStates.rooms }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">
                Jeg fant <span class="highlight">{{ numberToText(roomCount) }}</span> romnavn
              </span>
            </button>
            
            <div v-if="toggleStates.rooms" class="section-content">
              <p class="result-text">
                <span v-for="(room, index) in currentFile?.processedData?.room_names" :key="index">
                  <span 
                    class="field-name"
                    @mouseover="highlightBBox(room)"
                    @mouseout="clearHighlight"
                  >"{{ room }}"</span>
                  <span v-if="index < currentFile?.processedData?.room_names.length - 1" class="conjunction"> og </span>
                </span>
              </p>
            </div>
          </div>

          <!-- Other Information Section in Results Panel -->
          <div class="result-section">
            <button class="toggle-button" @click="toggleStates.otherInfo = !toggleStates.otherInfo">
              <svg :class="{ rotated: toggleStates.otherInfo }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">Jeg fant også denne informasjonen:</span>
            </button>
            
            <div v-if="toggleStates.otherInfo" class="section-content">
              <div v-if="currentFile?.processedData?.cardinal_direction" class="info-item">
                <span class="info-label">Himmelretning: </span>
                <span class="field-name">"{{ currentFile.processedData.cardinal_direction }}"</span>
              </div>
              <div v-if="currentFile?.processedData?.scale" class="info-item">
                <span class="info-label">Målestokk: </span>
                <span class="field-name">"{{ currentFile.processedData.scale }}"</span>
              </div>
              <div v-if="currentFile?.processedData?.gnr_bnr" class="info-item">
                <span class="info-label">Gnr/Bnr (gårdsnummer/bruksnummer): </span>
                <span class="field-name">"{{ currentFile.processedData.gnr_bnr }}"</span>
              </div>
            </div>
          </div>
        </div>
        <div class="feedback-panel">
          <h2 class="panel-title">Tilbakemelding til resultater</h2>
          
          <!-- Document Type Feedback -->
          <div class="result-section">
            <button class="toggle-button" @click="toggleStates.documentFeedback = !toggleStates.documentFeedback">
              <svg :class="{ rotated: toggleStates.documentFeedback }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">Tilbakemelding - dokumenttyper</span>
            </button>
            
            <div v-if="toggleStates.documentFeedback" class="section-content">
              <div v-for="(detection, index) in currentFile?.processedData?.detections" :key="index" class="feedback-item">
                <p class="feedback-question">
                  <span 
                    class="field-name"
                    @mouseover="highlightBBox(detection.drawing_type)"
                    @mouseout="clearHighlight"
                  >"{{ detection.drawing_type }}"</span>
                  <span class="question-text"> - Stemmer det at dette er en </span>
                  <span class="field-name">{{ detection.drawing_type }}</span>?
                </p>
                <div class="feedback-buttons">
                  <Button variant="secondary" size="sm" @click="handleFeedback({ type: detection.drawing_type, isCorrect: true })">Ja</Button>
                  <Button variant="secondary" size="sm" @click="handleFeedback({ type: detection.drawing_type, isCorrect: false })">Nei</Button>
                </div>
              </div>
            </div>
          </div>

          <!-- Room Names Feedback (only show if drawing_type includes 'plantegning') -->
          <div v-if="isFloorPlan" class="result-section">
            <button class="toggle-button" @click="toggleStates.roomFeedback = !toggleStates.roomFeedback">
              <svg :class="{ rotated: toggleStates.roomFeedback }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">Tilbakemelding - romnavn</span>
            </button>
            
            <div v-if="toggleStates.roomFeedback" class="section-content">
              <div v-for="(room, index) in currentFile?.processedData?.room_names" :key="index" class="feedback-item">
                <p class="feedback-question">
                  <span 
                    class="field-name"
                    @mouseover="highlightBBox(room)"
                    @mouseout="clearHighlight"
                  >"{{ room }}"</span>
                  <span class="question-text"> - Er dette riktig romnavn?</span>
                </p>
                <div class="feedback-buttons">
                  <Button variant="secondary" size="sm" @click="handleFeedback({ room, isCorrect: true })">Ja</Button>
                  <Button variant="secondary" size="sm" @click="handleFeedback({ room, isCorrect: false })">Nei</Button>
                </div>
              </div>
            </div>
          </div>

          <!-- Other Information Feedback Section -->
          <div class="result-section">
            <button class="toggle-button" @click="toggleStates.otherInfoFeedback = !toggleStates.otherInfoFeedback">
              <svg :class="{ rotated: toggleStates.otherInfoFeedback }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">Tilbakemelding - Annen informasjon</span>
            </button>
            
            <div v-if="toggleStates.otherInfoFeedback" class="section-content">
              <div v-if="currentFile?.processedData?.cardinal_direction" class="feedback-item">
                <p class="feedback-question">
                  <span class="info-label">Himmelretning: </span>
                  <span class="field-name">"{{ currentFile.processedData.cardinal_direction }}"</span>
                  <span class="question-text"> - Er dette riktig?</span>
                </p>
                <div class="feedback-buttons">
                  <Button variant="secondary" size="sm" @click="handleFeedback({ field: 'cardinal_direction', value: currentFile.processedData.cardinal_direction, isCorrect: true })">Ja</Button>
                  <Button variant="secondary" size="sm" @click="handleFeedback({ field: 'cardinal_direction', value: currentFile.processedData.cardinal_direction, isCorrect: false })">Nei</Button>
                </div>
              </div>
              
              <div v-if="currentFile?.processedData?.scale" class="feedback-item">
                <p class="feedback-question">
                  <span class="info-label">Målestokk: </span>
                  <span class="field-name">"{{ currentFile.processedData.scale }}"</span>
                  <span class="question-text"> - Er dette riktig?</span>
                </p>
                <div class="feedback-buttons">
                  <Button variant="secondary" size="sm" @click="handleFeedback({ field: 'scale', value: currentFile.processedData.scale, isCorrect: true })">Ja</Button>
                  <Button variant="secondary" size="sm" @click="handleFeedback({ field: 'scale', value: currentFile.processedData.scale, isCorrect: false })">Nei</Button>
                </div>
              </div>

              <div v-if="currentFile?.processedData?.gnr_bnr" class="feedback-item">
                <p class="feedback-question">
                  <span class="info-label">Gnr/Bnr (gårdsnummer/bruksnummer): </span>
                  <span class="field-name">"{{ currentFile.processedData.gnr_bnr }}"</span>
                  <span class="question-text"> - Er dette riktig?</span>
                </p>
                <div class="feedback-buttons">
                  <Button variant="secondary" size="sm" @click="handleFeedback({ field: 'gnr_bnr', value: currentFile.processedData.gnr_bnr, isCorrect: true })">Ja</Button>
                  <Button variant="secondary" size="sm" @click="handleFeedback({ field: 'gnr_bnr', value: currentFile.processedData.gnr_bnr, isCorrect: false })">Nei</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.results {
  padding: var(--spacing-2xl) 0;
}

.results__title {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
  font-size: var(--font-size-2xl);
  color: var(--neutral-700);
}

.results__content {
  max-width: 1200px;
  margin: 0 auto;
}

.results__details {
  margin-top: var(--spacing-xl);
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-xl);
}

.results__metadata,
.results__feedback {
  background: var(--neutral-100);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.metadata-item {
  color: var(--neutral-600);
}

.feedback-buttons {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.results__actions {
  margin-top: var(--spacing-xl);
  text-align: center;
}

.container {
  display: flex;
  padding: 0 30px;
  gap: 80px;
  margin-top: 145px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.document-viewer {
  width: 650px;
  height: 849px;
  background: white;
  border-radius: 5px;
  box-shadow: 4px 4px 20px rgba(46, 45, 48, 0.5);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 145px;
}

.file-title {
  width: 455px;
  height: 36px;
  margin: 0 auto;
  font-family: 'Poppins', sans-serif;
  font-size: 24px;
  font-weight: 400;
  color: #000;
  text-align: center;
  padding-top: 50px;
}

.viewer-content {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-picker {
  height: 150px;
  background: #F0F8F7;
  border-top: 1px solid #E0E0E0;
  border-radius: 0 0 5px 5px;
  display: flex;
  align-items: center;
  position: relative;
}

.thumbnail-container {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 87px;
  overflow-x: auto;
  padding: 0 50px;
  margin: 0 auto;
}

.thumbnail {
  width: 102px;
  height: 75px;
  border: 2px solid #D0D0D0;
  border-radius: 5px;
  overflow: hidden;
  cursor: pointer;
}

.thumbnail.active {
  border-color: #007AFF;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.arrow-button {
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  position: absolute;
}

.arrow-button.left {
  left: 50px;
}

.arrow-button.right {
  right: 50px;
}

.arrow-button svg path {
  stroke: #87A7A1;
}

.panel-title {
  font-family: 'Poppins', sans-serif;
  font-size: 24px;
  color: #000;
  margin-bottom: 20px;
  white-space: nowrap;
}

.toggle-button {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 10px 0;
}

.toggle-button svg {
  transition: transform 0.3s ease;
}

.toggle-button svg.rotated {
  transform: rotate(90deg);
}

.toggle-text {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
}

.highlight {
  color: #3D8B78;
  font-weight: 500;
}

.field-name {
  font-family: 'Poppins', sans-serif;
  font-weight: 700;
  font-size: 12px;
  color: #3D8B78;
  text-decoration: underline;
}

.section-content {
  padding: 10px 20px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.results-panel, .feedback-panel {
  width: 650px;
  height: 414.5px;
  background: white;
  border-radius: 5px;
  box-shadow: 4px 4px 20px rgba(46, 45, 48, 0.5);
  padding: 30px;
  overflow-y: auto;
}

.panel-title {
  height: 36px;
  margin: 0 auto;
  font-family: 'Poppins', sans-serif;
  font-size: 24px;
  font-weight: 400;
  color: #000;
  text-align: center;
  margin-bottom: 30px;
}

.result-section {
  margin-bottom: 20px;
}

.toggle-text {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
}

.highlight {
  color: #3D8B78;
  font-weight: bold;
}

.field-name {
  font-family: 'Poppins', sans-serif;
  font-weight: 700;
  font-size: 12px;
  color: #3D8B78;
  text-decoration: underline;
  cursor: pointer;
}

.conjunction {
  font-family: 'Poppins', sans-serif;
  font-size: 12px;
  color: #4A706A;
}

.section-content {
  margin-left: 30px;
  margin-top: 10px;
}

.feedback-panel {
  width: 650px;
  height: 414.5px;
  background: white;
  border-radius: 5px;
  box-shadow: 4px 4px 20px rgba(46, 45, 48, 0.5);
  padding: 30px;
  overflow-y: auto;
}

.feedback-item {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 5px;
  background: #F8F8F8;
}

.feedback-question {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
}

.question-text {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
}

.feedback-buttons {
  display: flex;
  gap: 10px;
  margin-left: 20px;
}

.info-item {
  margin-bottom: 10px;
}

.info-label {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
}
</style>
