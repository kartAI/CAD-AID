<script setup>
const props = defineProps({
  variant: {
    type: String,
    validator: (value) => ['primary', 'outline', 'success', 'error'].includes(value),
    default: 'primary'
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <button
    class="button"
    :class="[
      `button--${props.variant}`,
      `button--${props.size}`,
      { 'button--loading': props.loading }
    ]"
    :disabled="props.disabled || props.loading"
  >
    <span v-if="props.loading" class="button__loader"></span>
    <span class="button__content" :class="{ 'button__content--hidden': props.loading }">
      <slot></slot>
    </span>
  </button>
</template>

<style scoped>
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  min-width: 120px;
}

.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Variants */
.button--primary {
  background: var(--primary-color);
  color: white;
}

.button--primary:hover:not(:disabled) {
  background: var(--primary-dark);
}

.button--outline {
  background: transparent;
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.button--outline:hover:not(:disabled) {
  background: var(--primary-color);
  color: white;
}

.button--success {
  background: var(--success-color);
  color: white;
}

.button--success:hover:not(:disabled) {
  background: var(--success-dark);
}

.button--error {
  background: var(--error-color);
  color: white;
}

.button--error:hover:not(:disabled) {
  background: var(--error-dark);
}

/* Sizes */
.button--sm {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
}

.button--md {
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: var(--font-size-base);
}

.button--lg {
  padding: var(--spacing-lg) var(--spacing-xl);
  font-size: var(--font-size-lg);
}

/* Loading state */
.button--loading {
  color: transparent;
}

.button__loader {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: button-spin 0.6s linear infinite;
}

.button__content--hidden {
  visibility: hidden;
}

@keyframes button-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
