<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from '../components/common/Button.vue'
import apiService from '../services/api.js'

const router = useRouter()
const rating = ref(0)
const comment = ref('')
const isSubmitting = ref(false)
const error = ref(null)

const ratings = [
  { value: 1, label: 'Poor' },
  { value: 2, label: 'Fair' },
  { value: 3, label: 'Good' },
  { value: 4, label: 'Very Good' },
  { value: 5, label: 'Excellent' }
]

const handleSubmit = async () => {
  if (!rating.value) {
    error.value = 'Please select a rating'
    return
  }

  try {
    isSubmitting.value = true
    await apiService.submitFeedback({
      rating: rating.value,
      comment: comment.value
    })

    router.push({
      path: '/',
      query: { feedback: 'success' }
    })
  } catch (err) {
    error.value = 'Failed to submit feedback. Please try again.'
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="feedback">
    <div class="container">
      <h1 class="feedback__title">Your Feedback</h1>
      
      <div class="feedback__content">
        <div class="feedback__rating">
          <h3>How would you rate our service?</h3>
          <div class="rating-buttons">
            <button
              v-for="{ value, label } in ratings"
              :key="value"
              class="rating-button"
              :class="{ active: rating === value }"
              @click="rating = value"
            >
              {{ label }}
            </button>
          </div>
        </div>

        <div class="feedback__comment">
          <h3>Additional Comments</h3>
          <textarea
            v-model="comment"
            rows="4"
            placeholder="Tell us what you think..."
          ></textarea>
        </div>

        <p v-if="error" class="feedback__error">{{ error }}</p>

        <div class="feedback__actions">
          <Button
            variant="primary"
            size="lg"
            :loading="isSubmitting"
            @click="handleSubmit"
          >
            Submit Feedback
          </Button>
          <Button
            variant="outline"
            size="lg"
            :disabled="isSubmitting"
            @click="router.push('/')"
          >
            Skip
          </Button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.feedback {
  padding: var(--spacing-2xl) 0;
}

.feedback__title {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
  font-size: var(--font-size-2xl);
  color: var(--neutral-700);
}

.feedback__content {
  max-width: 600px;
  margin: 0 auto;
  background: var(--neutral-100);
  padding: var(--spacing-xl);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.feedback__rating,
.feedback__comment {
  margin-bottom: var(--spacing-xl);
}

.feedback__rating h3,
.feedback__comment h3 {
  margin-bottom: var(--spacing-md);
  color: var(--neutral-700);
}

.rating-buttons {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.rating-button {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--neutral-300);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--neutral-600);
  cursor: pointer;
  transition: all 0.2s ease;
}

.rating-button.active {
  border-color: var(--primary-color);
  background: var(--primary-color);
  color: white;
}

textarea {
  width: 100%;
  padding: var(--spacing-md);
  border: 2px solid var(--neutral-300);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--font-size-base);
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.feedback__error {
  color: var(--error-color);
  margin-bottom: var(--spacing-md);
  text-align: center;
}

.feedback__actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
}
</style>
