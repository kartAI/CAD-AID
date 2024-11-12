<script setup>
import norkartLogo from '@/assets/images/norkart-logo.svg'
import ebyggesokLogo from '@/assets/images/ebyggesøk.svg'
</script>

<template>
  <header class="header">
    <div class="header__content">
      <img :src="norkartLogo" alt="Norkart" class="header__logo" />
      <img :src="ebyggesokLogo" alt="eByggesøk" class="header__logo header__logo--right" />
    </div>
  </header>
</template>

<style scoped>
.header {
  height: 115px;
  background: #FFFFFF;
  border-bottom: 0.13px solid rgba(46, 45, 48, 0.12);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.25);
}

.header__content {
  height: 100%;
  max-width: 1440px;
  margin: 0 auto;
}

.header__logo {
  position: absolute;
  top: 35px;
  height: 45px;
  width: 247px;
  transition: opacity 0.2s ease;
}

.header__logo:first-child {
  left: 35px;
}

.header__logo--right {
  right: 35px;
}

.header__logo:hover {
  opacity: 0.8;
}
</style>
