<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/layout/Header.vue'
import Button from '../components/common/Button.vue'

const router = useRouter()

const handleBackToHome = () => {
  router.push('/')
}
</script>

<template>
  <main class="success">
    <Header />
    <div class="container">
      <div class="success-container">
        <div class="success-content">
          <h1 class="title">Prosessering fullført!</h1>
          <div class="success-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="32" fill="#24BD76" fill-opacity="0.1"/>
              <path d="M26 32L30 36L38 28" stroke="#24BD76" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="description">Alle filer er behandlet og tilbakemeldinger er sendt.</p>
          <Button 
            variant="primary"
            class="back-button"
            @click="handleBackToHome"
          >
            Tilbake til start
          </Button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.success {
  min-height: 100vh;
  background: linear-gradient(135deg, #DDF3EB 0%, #c5e9db 100%);
  padding-top: 115px;
}

.success-container {
  width: 600px;
  background: #FFFFFF;
  border-radius: 5px;
  margin: 214.5px auto 0;
  padding: 40px;
  box-shadow: 4px 4px 20px rgba(46, 45, 48, 0.5),
              0 0 30px rgba(36, 189, 118, 0.1);
  animation: fadeIn 0.5s ease-out;
}

.success-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.title {
  font-family: 'Poppins', sans-serif;
  font-weight: 600;
  font-size: 24px;
  color: #2E2D30;
  margin-bottom: 24px;
}

.success-icon {
  margin: 20px 0;
}

.description {
  font-family: 'Noto Sans', sans-serif;
  font-size: 16px;
  color: #666;
  margin-bottom: 32px;
}

.back-button {
  width: 265.3px;
  height: 52.74px;
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
</style>