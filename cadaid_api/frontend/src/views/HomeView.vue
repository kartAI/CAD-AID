<script setup>
import { useRouter } from 'vue-router'
import Button from '../components/common/Button.vue'
import kartaiLogo from '@/assets/images/kartai-logo.png'
import Header from '../components/layout/Header.vue'

const router = useRouter()

const navigateToUpload = () => {
  router.push('/upload')
}
</script>

<template>
  <main class="home">
    <Header />
    <div class="container">
      <div class="content-box">
        <div class="content-left">
          <h1 class="title">CAD-AID</h1>
          <p class="description description--first">
            Behandling av byggesaker krever tid og ressurser til validering av dokumenter og innhold.
          </p>
          <p class="description description--second">
            Vi har nå utviklet KI-modeller som samarbeider seg i mellom for å klassifisere og hente ut relevant informasjon fra dokumenter brukt i byggesak.
          </p>
          <p class="description description--third">
            Test ut CAD-AID ved å følge lenken på knappen under.
          </p>
          <Button 
            variant="primary" 
            size="lg"
            @click="navigateToUpload"
            class="cta-button"
          >
            Prøv CAD-AID her
          </Button>
        </div>
        <div class="content-right">
          <img :src="kartaiLogo" alt="KartAI Logo" class="kartai-logo" />
          <p class="kartai-caption">Utviklet som en del av KartAI-prosjektet</p>
        </div>
      </div>
    </div>
    <div class="scroll-indicator"></div>
  </main>
</template>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #DDF3EB 0%, #c5e9db 100%);
  padding-top: 115px;
  position: relative;
}

.home::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M54.627 0l.83.828-1.415 1.415L51.8 0h2.827zM5.373 0l-.83.828L5.96 2.243 8.2 0H5.374zM48.97 0l3.657 3.657-1.414 1.414L46.143 0h2.828zM11.03 0L7.372 3.657 8.787 5.07 13.857 0H11.03zm32.284 0L49.8 6.485 48.384 7.9l-7.9-7.9h2.83zM16.686 0L10.2 6.485 11.616 7.9l7.9-7.9h-2.83zM22.344 0L13.858 8.485 15.272 9.9l7.9-7.9h-.828zm5.656 0L19.515 8.485 17.343 10.657l7.9-7.9h2.757zm5.656 0L24.172 8.485 26.343 10.657l7.9-7.9h-.828zm5.656 0L29.828 8.485 32 10.657l7.9-7.9h-2.83zm5.657 0L35.485 8.485 37.657 10.657l7.9-7.9h-2.83zm5.657 0L41.142 8.485 39.314 10.313l7.9-7.9h-2.83zm5.657 0L46.8 8.485 45.385 9.9l7.9-7.9h-2.83zm5.657 0L52.456 8.485 54.627 10.657l7.9-7.9h-2.83zM32 0l1.414 1.414 16.97 16.97-1.414 1.415L32 2.828 14.03 20.8l-1.414-1.415L29.586 2.414 31 1 32 0zm0 18.686L13.314 37.373l-1.414-1.414L30.586 17.272 32 15.858l1.414 1.414 18.686 18.687-1.414 1.414L32 18.687zm0 18.686L13.314 56.06l-1.414-1.414L30.586 35.96 32 34.544l1.414 1.414 18.686 18.687-1.414 1.414L32 37.373z' fill='%2324bd76' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
}

.content-box {
  width: 960px;
  height: 444px;
  background: #FFFFFF;
  border-radius: 5px;
  margin: 205px auto 0;
  display: flex;
  padding: 35px 40px 40px 40px;
  box-sizing: border-box;
  box-shadow: 4px 4px 20px rgba(46, 45, 48, 0.5),
              0 0 30px rgba(36, 189, 118, 0.1);
  position: relative;
  animation: fadeIn 0.5s ease-out;
  transition: transform 0.3s ease;
}

.content-box:hover {
  transform: scale(1.005);
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

.content-left {
  width: 392px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.title {
  font-family: 'Noto Sans', sans-serif;
  font-weight: 600;
  font-size: 24px;
  color: #2E2D30;
  margin-bottom: 24px;
  margin-top: 6px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
}

.title::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: #24BD76;
  transition: width 0.3s ease;
}

.title:hover::after {
  width: 100%;
}

.description {
  font-family: 'Noto Sans', sans-serif;
  font-weight: 400;
  font-size: 16px;
  color: #000000;
  line-height: 22px;
  align-self: flex-start;
  background: linear-gradient(90deg, #000000 0%, #2E2D30 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.description--first {
  width: 392px;
  height: 44px;
  margin-bottom: 19px;
}

.description--second {
  width: 395px;
  height: 66px;
  margin-bottom: 19px;
}

.description--third {
  width: 392px;
  height: 43px;
  margin-bottom: 41px;
}

.cta-button {
  width: 247px;
  height: 56px;
  background: #24BD76;
  border-radius: 10px;
  font-family: 'Noto Sans Display', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #2E2D30;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.2s ease;
  animation: pulse 2s infinite;
}

.cta-button:hover {
  background: #1ea365;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

.content-right {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-left: auto;
  padding-right: 31px;
  margin-top: -10px;
}

.kartai-logo {
  width: 337px;
  height: 212px;
  object-fit: contain;
  margin-top: 21px;
  transition: filter 0.3s ease;
}

.kartai-logo:hover {
  filter: brightness(1.05);
}

.kartai-caption {
  font-family: 'Noto Sans', sans-serif;
  font-weight: 300;
  font-style: italic;
  font-size: 16px;
  color: #000000;
  width: 276px;
  height: 27px;
  line-height: 27px;
  text-align: center;
  margin-top: 5px;
  white-space: nowrap;
  animation: fadeInUp 0.8s ease-out 0.5s backwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.scroll-indicator {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 50px;
  border: 2px solid rgba(36, 189, 118, 0.3);
  border-radius: 15px;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.scroll-indicator::before {
  content: '';
  position: absolute;
  top: 8px;
  left: 50%;
  width: 6px;
  height: 6px;
  background: #24BD76;
  border-radius: 50%;
  transform: translateX(-50%);
  animation: scrollIndicator 2s infinite;
}

@keyframes scrollIndicator {
  0% { transform: translate(-50%, 0); opacity: 1; }
  100% { transform: translate(-50%, 20px); opacity: 0; }
}

.scroll-indicator:hover {
  opacity: 1;
}
</style>
