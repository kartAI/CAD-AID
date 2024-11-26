<script setup>
import { ref, onMounted, computed, watch } from 'vue'
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
  documentsResults: false,
  roomsResults: false,
  otherInfoResults: false,
  documentsFeedback: false,
  roomsFeedback: false,
  otherInfoFeedback: false
})
const highlightedArea = ref(null)
const feedbackProgress = ref({})

const currentFile = computed(() => results.value[activeFileIndex.value])

const documentCount = computed(() => {
  return currentFile.value?.processedData?.detections?.length || 0
})

const roomCount = computed(() => {
  return currentFile.value?.processedData?.room_names?.length || 0
})

const totalQuestions = computed(() => {
  if (!currentFile.value?.processedData) return 0
  if (!hasAnyContent.value) return 0
  
  let count = 0
  count += (currentFile.value.processedData.detections?.length || 0)
  count += (currentFile.value.processedData.room_names?.length || 0)
  count += (currentFile.value.processedData.cardinal_directions?.length || 0)
  count += (currentFile.value.processedData.scales?.length || 0)
  count += (currentFile.value.processedData.gnr_bnr_values?.length || 0)
  return count
})

const answeredQuestions = computed(() => {
  return Object.keys(feedbackProgress.value).filter(key => {
    const filePrefix = `file_${currentFile.value?.filename}_`
    return key.startsWith(filePrefix)
  }).length
})

const allQuestionsAnswered = computed(() => {
  if (!currentFile.value?.processedData) return true
  return answeredQuestions.value === totalQuestions.value && totalQuestions.value > 0
})

const totalFiles = computed(() => results.value.length)
const currentFileNumber = computed(() => activeFileIndex.value + 1)

const progressPercentage = computed(() => {
  if (!totalQuestions.value) return 0
  return Math.round((answeredQuestions.value / totalQuestions.value) * 100)
})

const getUniqueKey = (item, type, index) => {
  const filePrefix = `file_${currentFile.value?.filename}_`
  if (type === 'drawing') {
    return `${filePrefix}drawing_type_${item.drawing_type}_${index}`
  } else if (type === 'room') {
    return `${filePrefix}room_${item.name}_${index}`
  } else if (type === 'other') {
    return `${filePrefix}${item.field}_${item.value}_${index}`
  }
  return ''
}

const getFeedbackStatus = (item, type, index) => {
  const key = getUniqueKey(item, type, index)
  return feedbackProgress.value[key]
}

const handleFeedback = (item, type, index, isCorrect) => {
  const key = getUniqueKey(item, type, index)
  if (key) {
    feedbackProgress.value = {
      ...feedbackProgress.value,
      [key]: isCorrect
    }
  }
}

const getButtonClasses = (buttonType, item, type, index) => {
  const status = getFeedbackStatus(item, type, index)
  return {
    'feedback-button': true,
    [buttonType === 'yes' ? 'yes-button' : 'no-button']: true,
    'selected': buttonType === 'yes' ? status === true : status === false
  }
}

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
          cardinal_directions: file.detections?.flatMap(d => 
          Array.isArray(d.cardinal_direction) ? d.cardinal_direction : [d.cardinal_direction]
          ).filter(Boolean) || [],
          scales: [...new Set(
            file.detections?.flatMap(d =>
              Array.isArray(d.scale) ? d.scale : [d.scale]
            ).filter(Boolean) || []
          )],
          gnr_bnr_values: [...new Set(
            file.detections?.map(d => 
              Array.isArray(d.gnr_bnr) ? d.gnr_bnr[0] : d.gnr_bnr
            ).filter(Boolean) || []
          )]
      }
    }));
    console.log('Set results:', results.value)
  } catch (error) {
    console.error('Error:', error)
    router.push('/upload')
  }
})

const handleFileChange = (index) => {
  activeFileIndex.value = index
}

const submitFeedback = async () => {
  try {
    if (!hasAnyContent.value) {
      if (activeFileIndex.value < results.value.length - 1) {
        activeFileIndex.value++
      } else {
        router.push('/success')
      }
      return
    }

    await apiService.submitFeedback({
      filename: currentFile.value.filename,
      feedback: feedbackProgress.value
    })
    
    if (activeFileIndex.value < results.value.length - 1) {
      const currentFileName = currentFile.value.filename
      const currentFeedback = { ...feedbackProgress.value }
      
      activeFileIndex.value++
      
      feedbackProgress.value = {
        ...currentFeedback,
        ...feedbackProgress.value
      }
    } else {
      router.push('/success')
    }
  } catch (error) {
    console.error('Failed to submit feedback:', error)
    alert('Det oppstod en feil ved innsending av tilbakemelding. Vennligst prøv igjen.')
  }
}

const analyzeMore = () => {
  router.push('/upload')
}

const numberToText = (num) => {
  const numbers = ['null', 'ett', 'to', 'tre', 'fire', 'fem', 'seks', 'syv', 'åtte', 'ni', 'ti']
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

const highlightBBox = (detection) => {
  if (detection && detection.bbox) {
    highlightedArea.value = {
      bbox: detection.bbox,
      label: detection.drawing_type
    }
  }
}

const clearHighlight = () => {
  highlightedArea.value = null
}

const submitAllFeedback = async () => {
  try {
    await apiService.submitFeedback({
      filename: currentFile.value.filename,
      feedback: feedbackProgress.value
    })
    
    if (activeFileIndex.value === (results.value?.length - 1)) {
      router.push('/success')
    } else {
      activeFileIndex.value++
      feedbackProgress.value = {}
    }
  } catch (error) {
    console.error('Failed to submit feedback:', error)
  }
}

// Function to get button variant based on feedback state
const getButtonVariant = (type, isYes) => {
  const key = `drawing_type_${type}`
  if (feedbackProgress.value[key] === undefined) return 'outline'
  return feedbackProgress.value[key] === isYes ? (isYes ? 'success' : 'error') : 'outline'
}

const showNextButton = computed(() => {
  return activeFileIndex.value < results.value.length - 1
})

const showSubmitButton = computed(() => {
  return currentFile.value?.processedData && Object.keys(feedbackProgress.value).length > 0
})

// Single declaration of getFeedbackButtonVariant
const getFeedbackButtonVariant = (buttonType, { type, room, field, value }) => {
  const key = room ? 
    `room_${room}` : 
    type ? 
      `drawing_type_${type}` : 
      `${field}_${value}`
  
  const currentValue = feedbackProgress.value[key]
  
  if (buttonType === 'yes') {
    return currentValue === true ? 'success' : 'outline'
  }
  return currentValue === false ? 'error' : 'outline'
}

// Add computed properties to check for content
const hasDocuments = computed(() => 
  currentFile.value?.processedData?.detections?.length > 0
)

const hasRoomNames = computed(() => 
  currentFile.value?.processedData?.room_names?.length > 0
)

const hasOtherInfo = computed(() => {
  const data = currentFile.value?.processedData
  return Boolean(
    data?.cardinal_directions?.length > 0 || 
    data?.scales?.length > 0 || 
    data?.gnr_bnr_values?.length > 0
  )
})

const hasAnyFeedbackSections = computed(() => 
  hasDocuments.value || hasRoomNames.value || hasOtherInfo.value
)

const getFeedbackButtonClass = (buttonType, { type, room, field, value }) => {
  const key = room ? 
    `room_${room}` : 
    type ? 
      `drawing_type_${type}` : 
      `${field}_${value}`
  
  const currentValue = feedbackProgress.value[key]
  
  return {
    'feedback-button': true,
    [buttonType === 'yes' ? 'yes-button' : 'no-button']: true,
    'selected': buttonType === 'yes' ? currentValue === true : currentValue === false
  }
}

const completedFiles = computed(() => {
  return results.value.map((file, index) => {
    if (index < activeFileIndex.value) {
      return true
    }
    
    if (index === activeFileIndex.value) {
      if (!hasFileContent(file)) {
        return true
      }
      
      const filePrefix = `file_${file.filename}_`
      const fileQuestions = Object.keys(feedbackProgress.value)
        .filter(key => key.startsWith(filePrefix))
        .length
      
      const totalFileQuestions = getFileTotalQuestions(file)
      return fileQuestions === totalFileQuestions
    }
    
    return false
  })
})

const submitButtonText = computed(() => {
  if (!hasAnyContent.value) {
    return 'Neste fil'
  }
  if (!allQuestionsAnswered.value) {
    return 'Neste fil'
  }
  return activeFileIndex.value === results.value.length - 1 
    ? 'Send tilbakemelding' 
    : 'Neste fil'
})

const hasAnyContent = computed(() => {
  const data = currentFile.value?.processedData
  return Boolean(
    (data?.detections?.length > 0) ||
    (data?.room_names?.length > 0) ||
    data?.cardinal_directions?.length > 0 ||
    data?.scales?.length > 0 ||
    data?.gnr_bnr_values.length > 0
  )
})

const hasFileContent = (file) => {
  const data = file?.processedData
  return Boolean(
    (data?.detections?.length > 0) ||
    (data?.room_names?.length > 0) ||
    data?.cardinal_directions?.length > 0 ||
    data?.scales?.length > 0 ||
    data?.gnr_bnr_values?.length > 0
  )
}

const getFileTotalQuestions = (file) => {
  if (!file?.processedData) return 0
  let count = 0
  count += (file.processedData.detections?.length || 0)
  count += (file.processedData.room_names?.length || 0)
  if (file.processedData.cardinal_directions?.length) count++
  if (file.processedData.scales?.length) count++
  if (file.processedData.gnr_bnr_values?.length) count++
  return count
}

watch(activeFileIndex, (newIndex, oldIndex) => {
  if (newIndex > oldIndex) {
    const previousFile = results.value[oldIndex]
    if (previousFile) {
      const filePrefix = `file_${previousFile.filename}_`
      const currentFeedback = { ...feedbackProgress.value }
      
      feedbackProgress.value = {
        ...currentFeedback
      }
    }
  }
})
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
              :class="{ 
                active: index === activeFileIndex,
                completed: completedFiles[index]
              }"
              @click="handleFileChange(index)"
            >
              <img :src="file.url" :alt="file.filename">
              <div v-if="completedFiles[index]" class="completion-badge">
                <i class="fas fa-check"></i>
              </div>
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
          <div v-if="hasDocuments" class="result-section">
            <button class="toggle-button" @click="toggleStates.documentsResults = !toggleStates.documentsResults">
              <svg :class="{ rotated: toggleStates.documentsResults }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">
                Jeg fant <span class="highlight">{{ numberToText(documentCount) }}</span> dokumenter
              </span>
            </button>
            
            <div v-if="toggleStates.documentsResults" class="section-content">
              <p class="result-text">
                <span v-for="(detection, index) in currentFile?.processedData?.detections" :key="index">
                  <span class="field-name">"{{ detection.drawing_type }}"</span>
                  <span v-if="index < currentFile?.processedData?.detections.length - 1" class="conjunction"> og </span>
                </span>
              </p>
            </div>
          </div>

          <!-- Rooms Section (only show if drawing_type includes 'plantegning' AND has room names) -->
          <div v-if="hasRoomNames" class="result-section">
            <button class="toggle-button" @click="toggleStates.roomsResults = !toggleStates.roomsResults">
              <svg :class="{ rotated: toggleStates.roomsResults }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">
                Jeg fant <span class="highlight">{{ numberToText(roomCount) }}</span> romnavn
              </span>
            </button>
            
            <div v-if="toggleStates.roomsResults" class="section-content">
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

          <!-- Other Information Section (only show if any other info exists) -->
          <div v-if="hasOtherInfo" class="result-section">
            <button class="toggle-button" @click="toggleStates.otherInfoResults = !toggleStates.otherInfoResults">
              <svg :class="{ rotated: toggleStates.otherInfoResults }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
              </svg>
              <span class="toggle-text">Jeg fant også denne informasjonen:</span>
            </button>
            
            <div v-if="toggleStates.otherInfoResults" class="section-content">
              <div v-if="currentFile?.processedData?.cardinal_directions?.length" class="info-item">
                <span class="info-label">Himmelretninger: </span>
                <span v-for="(direction, index) in currentFile.processedData.cardinal_directions" :key="index">
                  <span class="field-name">"{{ direction }}"</span>
                  <span v-if="index < currentFile.processedData.cardinal_directions.length - 1" class="conjunction"> og </span>
                </span>
              <div v-if="currentFile?.processedData?.scales?.length" class="info-item">
                <span class="info-label">Målestokk: </span>
                <span v-for="(scale, index) in currentFile.processedData.scales" :key="index">
                  <span class="field-name">"{{ scale }}"</span>
                  <span v-if="index < currentFile.processedData.scales.length - 1" class="conjunction"> og </span>
                  </span>
                </div>
              </div>
              <div v-if="currentFile?.processedData?.gnr_bnr_values?.length" class="info-item">
                <span class="info-label">Gnr/Bnr (gårdsnummer/bruksnummer): </span>
                <span v-for="(gnrBnr, index) in currentFile.processedData.gnr_bnr_values" :key="index">
                  <span class="field-name">"{{ gnrBnr }}"</span>
                  <span v-if="index < currentFile.processedData.gnr_bnr_values.length - 1" class="conjunction"> og </span>
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="feedback-panel">
          <h2 class="panel-title">Tilbakemelding til resultater</h2>
          
          <!-- Show message if no content -->
          <div v-if="!hasAnyContent" class="no-content-message">
            Ingen innhold å validere i denne filen
          </div>
          
          <!-- Only show feedback sections if there's content -->
          <template v-else>
            <!-- Global feedback counter -->
            <div v-if="hasAnyFeedbackSections" class="feedback-counter">
              <span>{{ answeredQuestions }} av {{ totalQuestions }} spørsmål besvart</span>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${(answeredQuestions / totalQuestions) * 100}%` }"
                ></div>
              </div>
            </div>
            
            <!-- Document Types Section -->
            <div v-if="hasDocuments" class="result-section">
              <button class="toggle-button" @click="toggleStates.documentsFeedback = !toggleStates.documentsFeedback">
                <svg :class="{ rotated: toggleStates.documentsFeedback }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                  <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
                </svg>
                <span class="toggle-text">Tilbakemelding - tegningstyper</span>
              </button>
              
              <div v-if="toggleStates.documentsFeedback" class="section-content">
                <div v-for="(detection, index) in currentFile?.processedData?.detections" 
                     :key="getUniqueKey(detection, 'drawing', index)" 
                     class="feedback-item">
                  <p class="feedback-question">
                    <span 
                      class="field-name"
                      @mouseover="highlightBBox(detection)"
                      @mouseout="clearHighlight"
                    >"{{ detection.drawing_type }}"</span>
                    <span class="question-text"> - Er dette riktig tegningstype?</span>
                  </p>
                  <div class="feedback-buttons">
                    <Button 
                      variant="outline"
                      :class="getButtonClasses('yes', detection, 'drawing', index)"
                      @click="handleFeedback(detection, 'drawing', index, true)"
                    >
                      Ja
                    </Button>
                    <Button 
                      variant="outline"
                      :class="getButtonClasses('no', detection, 'drawing', index)"
                      @click="handleFeedback(detection, 'drawing', index, false)"
                    >
                      Nei
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Room Names Feedback (only show if drawing_type includes 'plantegning') -->
            <div v-if="currentFile?.processedData?.room_names?.length > 0" class="result-section">
              <button class="toggle-button" @click="toggleStates.roomsFeedback = !toggleStates.roomsFeedback">
                <svg :class="{ rotated: toggleStates.roomsFeedback }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                  <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
                </svg>
                <span class="toggle-text">Tilbakemelding - rom navn</span>
              </button>
              
              <div v-if="toggleStates.roomsFeedback" class="section-content">
                <div v-for="(room, index) in currentFile?.processedData?.room_names" 
                     :key="getUniqueKey({ name: room }, 'room', index)" 
                     class="feedback-item">
                  <p class="feedback-question">
                    <span 
                      class="field-name"
                      @mouseover="highlightBBox(room)"
                      @mouseout="clearHighlight"
                    >"{{ room }}"</span>
                    <span class="question-text"> - Er dette riktig romnavn?</span>
                  </p>
                  <div class="feedback-buttons">
                    <Button 
                      variant="outline"
                      :class="getButtonClasses('yes', { name: room }, 'room', index)"
                      @click="handleFeedback({ name: room }, 'room', index, true)"
                    >
                      Ja
                    </Button>
                    <Button 
                      variant="outline"
                      :class="getButtonClasses('no', { name: room }, 'room', index, false)"
                      @click="handleFeedback({ name: room }, 'room', index, false)"
                    >
                      Nei
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Other Information Feedback Section -->
            <div v-if="hasOtherInfo" class="result-section">
              <button class="toggle-button" @click="toggleStates.otherInfoFeedback = !toggleStates.otherInfoFeedback">
                <svg :class="{ rotated: toggleStates.otherInfoFeedback }" width="10" height="20" viewBox="0 0 10 20" fill="none">
                  <path d="M2 2L8 10L2 18" stroke="#87A7A1" stroke-width="2"/>
                </svg>
                <span class="toggle-text">Tilbakemelding - Annen informasjon</span>
              </button>
              
              <div v-if="toggleStates.otherInfoFeedback" class="section-content">
                <div v-for="(direction, index) in currentFile?.processedData?.cardinal_directions" :key="`direction_${index}`" class="feedback-item">
                  <p class="feedback-question">
                    <span class="field-name">"{{ direction }}"</span>
                    <span class="question-text"> - Er dette riktig himmelretning?</span>
                  </p>
                  <div class="feedback-buttons">
                    <Button 
                      variant="outline"
                      :class="getButtonClasses('yes', { field: 'cardinal_directions', value: direction }, 'other', index)"
                      @click="handleFeedback({ field: 'cardinal_directions', value: direction }, 'other', index, true)"
                    >
                      Ja
                    </Button>
                    <Button 
                      variant="outline"
                      :class="getButtonClasses('no', { field: 'cardinal_directions', value: direction }, 'other', index)"
                      @click="handleFeedback({ field: 'cardinal_directions', value: direction }, 'other', index, false)"
                    >
                      Nei
                    </Button>
                  </div>
                </div>
                <div v-for="(scale, index) in currentFile?.processedData?.scales" :key="`scale_${index}`" class="feedback-item">
                  <p class="feedback-question">
                    <span class="field-name">"{{ scale }}"</span>
                    <span class="question-text"> - Er dette riktig målestokk?</span>
                  </p>
                  <div class="feedback-buttons">
                    <Button
                      variant="outline"
                      :class="getButtonClasses('yes', { field: 'scales', value: scale }, 'other', index)"
                      @click="handleFeedback({ field: 'scales', value: scale }, 'other', 0, true)"
                    >
                      Ja
                    </Button>
                    <Button
                      variant="outline"
                      :class="getButtonClasses('no', { field: 'scales', value: scale }, 'other', 0)"
                      @click="handleFeedback({ field: 'scales', value: scale }, 'other', 0, false)"
                    >
                      Nei
                    </Button>
                  </div>
                </div>
                <div v-for="(gnrBnr, index) in currentFile?.processedData?.gnr_bnr_values" :key="`gnr_bnr_${index}`" class="feedback-item">
                  <p class="feedback-question">
                    <span class="field-name">"{{ gnrBnr }}"</span>
                    <span class="question-text"> - Er dette riktig Gnr/Bnr?</span>
                  </p>
                  <div class="feedback-buttons">
                    <Button
                      variant="outline"
                      :class="getButtonClasses('yes', { field: 'gnr_bnr_values', value: gnrBnr }, 'other', index)"
                      @click="handleFeedback({ field: 'gnr_bnr_values', value: gnrBnr }, 'other', index, true)"
                    >
                      Ja
                    </Button>
                    <Button
                      variant="outline"
                      :class="getButtonClasses('no', { field: 'gnr_bnr_values', value: gnrBnr }, 'other', index)"
                      @click="handleFeedback({ field: 'gnr_bnr_values', value: gnrBnr }, 'other', index, false)"
                    >
                      Nei
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
        <div class="action-buttons">
          <Button 
            variant="!hasAnyContent || allQuestionsAnswered ? 'primary' : 'outline'"
            @click="!hasAnyContent || allQuestionsAnswered ? submitFeedback() : nextFile()"
          >
            {{ submitButtonText }}
          </Button>
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
  gap: 8px;
}

:deep(.button) {
  min-width: 60px;
  height: 32px;
  padding: 0 12px;
  font-size: 14px;
}

:deep(.button.success) {
  background-color: #24BD76;
  border-color: #24BD76;
  color: white;
}

:deep(.button.error) {
  background-color: #FF4D4F;
  border-color: #FF4D4F;
  color: white;
}

:deep(.button.outline) {
  background-color: transparent;
}

:deep(.button.outline.yes-button) {
  border-color: #24BD76;
  color: #24BD76;
}

:deep(.button.outline.yes-button:hover) {
  background-color: rgba(36, 189, 118, 0.1);
}

:deep(.button.outline.no-button) {
  border-color: #FF4D4F;
  color: #FF4D4F;
}

:deep(.button.outline.no-button:hover) {
  background-color: rgba(255, 77, 79, 0.1);
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
  position: relative;
}

.thumbnail.active {
  border-color: #007AFF;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail.completed::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(36, 189, 118, 0.1);
  border: 2px solid #24BD76;
  border-radius: 3px;
}

.completion-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #24BD76;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
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

.feedback-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 2px solid #87A7A1;
  border-radius: 4px;
  background: white;
  color: #87A7A1;
  transition: all 0.2s;
}

.feedback-btn:hover {
  background: #f5f5f5;
}

.feedback-btn.active {
  background: #87A7A1;
  color: white;
}

.feedback-submit {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.progress-text {
  color: #4A706A;
  font-size: 14px;
}

.submit-button {
  margin-top: 20px;
  width: 100%;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-progress {
  margin-bottom: 20px;
  text-align: center;
}

.file-count {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
  margin-bottom: 8px;
  display: block;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #E5E5E5;
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
}

.progress-fill {
  height: 100%;
  background: #3D8B78;
  transition: width 0.3s ease;
}

.progress-text {
  font-family: 'Poppins', sans-serif;
  font-size: 12px;
  color: #4A706A;
}

.file-progress {
  margin: 20px auto;
  max-width: 600px;
  text-align: center;
  padding: 0 20px;
}

.file-count {
  font-family: 'Poppins', sans-serif;
  font-size: 16px;
  color: #4A706A;
  margin-bottom: 8px;
  display: block;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #E5E5E5;
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
}

.progress-fill {
  height: 100%;
  background: #3D8B78;
  transition: width 0.3s ease;
}

.progress-text {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
}

:deep(.button.success) {
  background-color: #24BD76 !important;
  color: white !important;
  border-color: #24BD76 !important;
}

:deep(.button.error) {
  background-color: #FF4D4F !important;
  color: white !important;
  border-color: #FF4D4F !important;
}

.feedback-section {
  margin: 20px 0;
}

.feedback-count {
  display: block;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  color: #4A706A;
  margin-bottom: 10px;
  text-align: center;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

:deep(.button.success) {
  background-color: #24BD76 !important;
  color: white !important;
  border-color: #24BD76 !important;
}

:deep(.button.error) {
  background-color: #FF4D4F !important;
  color: white !important;
  border-color: #FF4D4F !important;
}

.progress-indicator {
  margin: 20px auto;
  max-width: 600px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.progress-text {
  font-size: 14px;
  color: #4A706A;
  margin-bottom: 8px;
  display: block;
}

.progress-bar {
  height: 4px;
  background: #E5E5E5;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3D8B78;
  transition: width 0.3s ease;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
  margin: 16px 0;
}

.yes-button:hover {
  background-color: #24BD76 !important;
  color: white !important;
}

.no-button:hover {
  background-color: #FF4D4F !important;
  color: white !important;
}

.selected.yes-button {
  background-color: #1A8C58 !important;
  color: white !important;
}

.selected.no-button {
  background-color: #D93E40 !important;
  color: white !important;
}

.action-buttons {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

/* Yes button styles */
.yes-button {
  border-color: #24BD76 !important;
  color: #24BD76 !important;
}

.yes-button:hover {
  background-color: #24BD76 !important;
  color: white !important;
}

.selected-yes {
  background-color: #24BD76 !important;
  color: white !important;
}

/* No button styles */
.no-button {
  border-color: #FF4D4F !important;
  color: #FF4D4F !important;
}

.no-button:hover {
  background-color: #FF4D4F !important;
  color: white !important;
}

.selected-no {
  background-color: #FF4D4F !important;
  color: white !important;
}

.feedback-counter {
  margin: 20px 0;
  padding: 16px;
  background: var(--neutral-50);
  border-radius: var(--radius-lg);
  text-align: center;
}

.progress-bar {
  margin-top: 8px;
  width: 100%;
  height: 4px;
  background: var(--neutral-200);
  border-radius: 2px;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.feedback-button {
  transition: all 0.2s ease;
}

.yes-button:hover {
  background-color: var(--success-light) !important;
  border-color: var(--success-color) !important;
  color: var(--success-color) !important;
}

.yes-button.selected {
  background-color: var(--success-color) !important;
  border-color: var(--success-color) !important;
  color: white !important;
}

.no-button:hover {
  background-color: var(--error-light) !important;
  border-color: var(--error-color) !important;
  color: var(--error-color) !important;
}

.no-button.selected {
  background-color: var(--error-color) !important;
  border-color: var(--error-color) !important;
  color: white !important;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
}

.feedback-counter {
  margin: 20px 0;
  padding: 16px;
  background: var(--neutral-50);
  border-radius: var(--radius-lg);
  text-align: center;
}

.feedback-button {
  min-width: 60px;
  height: 32px;
  transition: all 0.2s ease;
}

.yes-button {
  border-color: var(--success-color) !important;
  color: var(--success-color) !important;
}

.yes-button:hover {
  background-color: var(--success-light) !important;
}

.yes-button.selected {
  background-color: var(--success-color) !important;
  color: white !important;
}

.no-button {
  border-color: var(--error-color) !important;
  color: var(--error-color) !important;
}

.no-button:hover {
  background-color: var(--error-light) !important;
}

.no-button.selected {
  background-color: var(--error-color) !important;
  color: white !important;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.feedback-item {
  margin-bottom: 16px;
}

:root {
  --success-color: #24BD76;
  --success-light: rgba(36, 189, 118, 0.1);
  --error-color: #FF4D4F;
  --error-light: rgba(255, 77, 79, 0.1);
}

.feedback-button {
  min-width: 60px;
  height: 32px;
}

.yes-button {
  border-color: var(--success-color) !important;
  color: var(--success-color) !important;
}

.yes-button:hover {
  background-color: rgba(36, 189, 118, 0.1) !important;
}

.yes-button.selected {
  background-color: rgba(36, 189, 118, 0.2) !important;
  border-color: var(--success-color) !important;
  color: var(--success-color) !important;
  font-weight: bold !important;
}

.no-button {
  border-color: var(--error-color) !important;
  color: var(--error-color) !important;
}

.no-button:hover {
  background-color: rgba(255, 77, 79, 0.1) !important;
}

.no-button.selected {
  background-color: rgba(255, 77, 79, 0.2) !important;
  border-color: var(--error-color) !important;
  color: var(--error-color) !important;
  font-weight: bold !important;
}

.thumbnail {
  position: relative;
}

.completion-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #24BD76;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.thumbnail.completed::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(36, 189, 118, 0.1);
  border: 2px solid #24BD76;
  border-radius: 3px;
}

.no-content-message {
  text-align: center;
  padding: 2rem;
  color: var(--neutral-500);
  font-style: italic;
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.action-buttons button {
  min-width: 120px;
}

.feedback-panel {
  background: linear-gradient(to bottom, #ffffff, #f8fdfb);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  padding: 24px;
  transition: transform 0.2s ease;
}

.feedback-panel:hover {
  transform: translateY(-2px);
}

.thumbnail {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.thumbnail:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.thumbnail.active {
  border: 3px solid #24BD76;
  box-shadow: 0 0 0 3px rgba(36, 189, 118, 0.2);
}

.completion-badge {
  transform: scale(0.9);
  transition: transform 0.2s ease;
}

.thumbnail:hover .completion-badge {
  transform: scale(1);
}

.feedback-counter {
  background: linear-gradient(135deg, #f0f9f6 0%, #e6f4ef 100%);
  border-radius: 12px;
  padding: 16px;
  margin: 20px 0;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
}

.progress-bar {
  background: rgba(36, 189, 118, 0.1);
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, #24BD76, #3BAF8F);
  box-shadow: 0 2px 4px rgba(36, 189, 118, 0.2);
  transition: width 0.5s ease;
}

.action-buttons button {
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(36, 189, 118, 0.2);
}

.action-buttons button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(36, 189, 118, 0.3);
}

.panel-title {
  font-size: 1.5rem;
  color: #2E2D30;
  margin-bottom: 1.5rem;
  position: relative;
  padding-bottom: 0.5rem;
}

.panel-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #24BD76, transparent);
  border-radius: 3px;
}

/* Enhanced feedback panel styling */
.feedback-panel {
  background: linear-gradient(145deg, #ffffff, #f8fdfb);
  border-radius: 16px;
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.05),
    0 0 0 1px rgba(36, 189, 118, 0.1);
  padding: 28px;
  transition: all 0.3s ease;
}

/* Enhanced toggle button styling */
.toggle-button {
  width: 100%;
  padding: 12px 16px;
  border-radius: 8px;
  background: linear-gradient(to right, rgba(36, 189, 118, 0.05), transparent);
  transition: all 0.3s ease;
}

.toggle-button:hover {
  background: linear-gradient(to right, rgba(36, 189, 118, 0.1), transparent);
  transform: translateX(4px);
}

/* Enhanced feedback item styling */
.feedback-item {
  background: linear-gradient(145deg, #ffffff, #f9f9f9);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.02),
    0 0 0 1px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.feedback-item:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.05),
    0 0 0 1px rgba(0, 0, 0, 0.03);
}

/* Enhanced field name styling */
.field-name {
  position: relative;
  padding: 2px 8px;
  background: rgba(36, 189, 118, 0.1);
  border-radius: 4px;
  transition: all 0.2s ease;
}

.field-name:hover {
  background: rgba(36, 189, 118, 0.15);
  transform: translateY(-1px);
}

/* Enhanced thumbnail container */
.thumbnail-container {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(to right, rgba(36, 189, 118, 0.05), transparent);
  border-radius: 12px;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(36, 189, 118, 0.3) transparent;
}

.thumbnail-container::-webkit-scrollbar {
  height: 6px;
}

.thumbnail-container::-webkit-scrollbar-thumb {
  background: rgba(36, 189, 118, 0.3);
  border-radius: 3px;
}

/* Enhanced completion badge */
.completion-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #24BD76, #1ea365);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(36, 189, 118, 0.3);
  transform: scale(0.9);
  transition: all 0.3s ease;
}

/* Enhanced progress bar */
.progress-bar {
  background: linear-gradient(to right, rgba(36, 189, 118, 0.1), rgba(36, 189, 118, 0.05));
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
}

.progress-fill {
  background: linear-gradient(90deg, #24BD76, #3BAF8F);
  box-shadow: 
    0 2px 4px rgba(36, 189, 118, 0.2),
    0 0 0 1px rgba(36, 189, 118, 0.1);
  animation: shimmer 2s infinite linear;
}

@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

/* Enhanced action buttons */
.action-buttons button {
  background: linear-gradient(135deg, #24BD76, #1ea365);
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 
    0 4px 12px rgba(36, 189, 118, 0.2),
    0 0 0 1px rgba(36, 189, 118, 0.1);
}

.action-buttons button:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 6px 16px rgba(36, 189, 118, 0.3),
    0 0 0 1px rgba(36, 189, 118, 0.2);
}

/* Add smooth scrolling */
html {
  scroll-behavior: smooth;
}

/* Add loading animations */
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.loading {
  animation: pulse 1.5s infinite ease-in-out;
}
</style>
