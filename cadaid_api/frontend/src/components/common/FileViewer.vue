<script setup>
import { ref, onMounted, watch, computed, onUnmounted, nextTick } from 'vue'
import { useElementSize } from '@vueuse/core'

const props = defineProps({
  file: {
    type: Object,
    default: null
  },
  highlightedArea: {
    type: Object,
    default: null
  }
})

const containerRef = ref(null)
const imageRef = ref(null)
const imageError = ref(false)
const scale = ref(1)
const position = ref({ x: 0, y: 0 })
const isZoomed = computed(() => scale.value > 1)

// Transform style for panning and zooming
const transformStyle = computed(() => {
  return {
    transform: `translate(${position.value.x}px, ${position.value.y}px) scale(${scale.value})`,
    transition: scale.value === 1 ? 'transform 0.3s ease' : 'none'
  }
})

// Handle drag
const isDragging = ref(false)
const startPos = ref({ x: 0, y: 0 })

const handleMouseDown = (e) => {
  if (!isZoomed.value) return
  isDragging.value = true
  startPos.value = {
    x: e.clientX - position.value.x,
    y: e.clientY - position.value.y
  }
}

const handleMouseMove = (e) => {
  if (!isDragging.value) return
  position.value = {
    x: e.clientX - startPos.value.x,
    y: e.clientY - startPos.value.y
  }
}

const handleMouseUp = () => {
  isDragging.value = false
}

// Wheel handler for zoom
const handleWheel = (e) => {
  // Prevent zooming behavior when ctrl/cmd is pressed
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    return
  }
  
  // Allow normal scrolling with trackpad/mouse
  const container = containerRef.value
  if (container) {
    // For trackpad gestures
    if (e.deltaMode === 0) {
      container.scrollLeft += e.deltaX
      container.scrollTop += e.deltaY
    } else {
      // For mouse wheel
      container.scrollLeft += e.deltaX * 16
      container.scrollTop += e.deltaY * 16
    }
  }
}

// Reset state when file changes
watch(() => props.file, () => {
  imageError.value = false
  scale.value = 1
  position.value = { x: 0, y: 0 }
})

// Add event listeners
onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseup', handleMouseUp)
  containerRef.value?.addEventListener('wheel', handleWheel, { passive: false })
})

// Clean up event listeners
onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
  containerRef.value?.removeEventListener('wheel', handleWheel)
})

// Add zoom control functions
const zoomIn = () => {
  const newScale = Math.min(scale.value + 0.5, 3);
  if (newScale !== scale.value) {
    const container = containerRef.value;
    
    // Get container dimensions and scroll position
    const viewportWidth = container.clientWidth;
    const viewportHeight = container.clientHeight;
    const scrollLeft = container.scrollLeft;
    const scrollTop = container.scrollTop;
    
    // Calculate center point of current viewport
    const centerX = scrollLeft + (viewportWidth / 2);
    const centerY = scrollTop + (viewportHeight / 2);
    
    scale.value = newScale;
    
    nextTick(() => {
      // Calculate new scroll position to maintain center point
      const newScrollLeft = (centerX * (newScale / (newScale - 0.5))) - (viewportWidth / 2);
      const newScrollTop = (centerY * (newScale / (newScale - 0.5))) - (viewportHeight / 2);
      
      container.scrollTo({
        left: newScrollLeft,
        top: newScrollTop,
        behavior: 'instant'
      });
    });
  }
};

const zoomOut = () => {
  const newScale = Math.max(scale.value - 0.5, 1);
  if (newScale !== scale.value) {
    const container = containerRef.value;
    
    // Get container dimensions and scroll position
    const viewportWidth = container.clientWidth;
    const viewportHeight = container.clientHeight;
    const scrollLeft = container.scrollLeft;
    const scrollTop = container.scrollTop;
    
    // Calculate center point of current viewport
    const centerX = scrollLeft + (viewportWidth / 2);
    const centerY = scrollTop + (viewportHeight / 2);
    
    scale.value = newScale;
    
    nextTick(() => {
      // Calculate new scroll position to maintain center point
      const newScrollLeft = (centerX * (newScale / (newScale + 0.5))) - (viewportWidth / 2);
      const newScrollTop = (centerY * (newScale / (newScale + 0.5))) - (viewportHeight / 2);
      
      container.scrollTo({
        left: newScrollLeft,
        top: newScrollTop,
        behavior: 'instant'
      });
    });
  }
};


const resetZoom = () => {
  scale.value = 1
  position.value = { x: 0, y: 0 }
  const container = containerRef.value
  
  // Reset all scroll positions
  container.scrollTo({
    left: 0,
    top: 0,
    behavior: 'instant'
  })
  
  // Reset any transforms
  const imageContainer = container.querySelector('.image-container')
  if (imageContainer) {
    imageContainer.style.transform = 'none'
  }
}

// Replace the highlightStyle computed property (lines 115-131):
const highlightStyle = computed(() => {
  if (!props.highlightedArea?.bbox || !imageRef.value) {
    return { display: 'none' }
  }

  try {
    const { width, height } = imageRef.value.getBoundingClientRect()
    const [x1, y1, x2, y2] = props.highlightedArea.bbox
    
    if (!Number.isFinite(x1) || !Number.isFinite(y1) || 
        !Number.isFinite(x2) || !Number.isFinite(y2)) {
      console.log('Invalid bbox:', props.highlightedArea.bbox)
      return { display: 'none' }
    }

    return {
      left: `${x1}px`,
      top: `${y1}px`,
      width: `${x2 - x1}px`,
      height: `${y2 - y1}px`,
      border: '3px dashed #87A7A1',
      backgroundColor: 'rgba(135, 167, 161, 0.1)',
      animation: 'dash 3s linear infinite'
    }
  } catch (error) {
    console.error('Error computing highlight:', error)
    return { display: 'none' }
  }
})

const isLoading = ref(true)

const highlightBBox = (item) => {
  console.log('Highlighting:', item)
  const detection = currentFile.value?.processedData?.detections?.find(
    d => d.drawing_type?.toLowerCase() === item.toLowerCase()
  )
  console.log('Found detection:', detection)
  if (detection) {
    highlightedArea.value = {
      bbox: detection.bbox,
      label: detection.drawing_type
    }
  }
}

const toggleFullscreen = () => {
  const viewer = containerRef.value
  if (!document.fullscreenElement) {
    viewer.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}
</script>

<template>
  <div class="file-viewer" ref="containerRef">
    <div class="viewer-controls">
      <button @click="zoomOut" class="control-button" title="Zoom Out">
        <i class="fas fa-search-minus"></i>
      </button>
      <button @click="resetZoom" class="control-button" title="Reset View">
        <i class="fas fa-compress-arrows-alt"></i>
      </button>
      <button @click="zoomIn" class="control-button" title="Zoom In">
        <i class="fas fa-search-plus"></i>
      </button>
      <button @click="toggleFullscreen" class="control-button" title="Fullscreen">
        <i class="fas fa-expand"></i>
      </button>
    </div>

    <div 
      class="preview-content"
      @mousedown="handleMouseDown"
    >
      <div 
        class="image-container"
        :style="transformStyle"
      >
        <img 
          v-if="file?.url" 
          :src="file.url" 
          :alt="file.filename"
          class="preview-image"
          ref="imageRef"
          @load="isLoading = false"
          @error="imageError = true; isLoading = false"
        />
        <div v-if="isLoading" class="loading-spinner">
          <!-- Add your loading spinner here -->
        </div>
        <div v-if="imageError" class="error-message">
          Failed to load image
        </div>
        <div 
          v-if="highlightedArea"
          class="highlight-overlay"
          :style="highlightStyle"
          v-show="props.highlightedArea"
        >
          <span class="highlight-label">{{ highlightedArea.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-viewer {
  position: relative;
  width: 100%;
  height: calc(100% - 86px);
  margin-top: 86px;
  overflow: hidden;
  background: white;
}

.viewer-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.control-button {
  background: rgba(135, 167, 161, 0.9);
  border: none;
  border-radius: 4px;
  padding: 8px;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.control-button:hover {
  background: rgba(135, 167, 161, 1);
}

.preview-content {
  width: 100%;
  height: 100%;
  overflow: scroll;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;
  scrollbar-gutter: stable;
}

.preview-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
  background-color: #f1f1f1;
}

.preview-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.preview-content::-webkit-scrollbar-thumb {
  background: #87A7A1;
  border-radius: 4px;
  min-height: 40px;
}

.preview-content::-webkit-scrollbar-corner {
  background: #f1f1f1;
}

.image-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: min-content;
  min-height: min-content;
  transform-origin: top left; /* Add this line */
}


.preview-image {
  max-width: 100%;
  max-height: 100%;
  transform-origin: top left;
  transform: scale(var(--scale, 1));
  transition: transform 0.2s ease-out;
}

.highlight-overlay {
  position: absolute;
  pointer-events: none;
  z-index: 2;
}

@keyframes dash {
  0% {
    border-style: dashed;
    border-color: rgba(135, 167, 161, 1);
    box-shadow: 0 0 0 0 rgba(135, 167, 161, 0.4);
  }
  50% {
    border-style: solid;
    border-color: rgba(135, 167, 161, 0.6);
    box-shadow: 0 0 10px 2px rgba(135, 167, 161, 0.2);
  }
  100% {
    border-style: dashed;
    border-color: rgba(135, 167, 161, 1);
    box-shadow: 0 0 0 0 rgba(135, 167, 161, 0.4);
  }
}

.highlight-label {
  position: absolute;
  top: -30px;
  left: 0;
  background: #87A7A1;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Transition animations for file changes */
.preview-image {
  transition: opacity 0.3s ease;
}

.preview-image[v-cloak] {
  opacity: 0;
}

.viewer-content {
  flex: 1;
  position: relative;
  overflow: visible;
  display: flex;
  flex-direction: column;
}

.file-title {
  position: absolute;
  top: -86px;
  left: 0;
  right: 0;
  z-index: 1;
}
</style> 