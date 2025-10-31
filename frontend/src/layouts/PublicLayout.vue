<template>
  <div class="public-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 公共布局组件
</script>

<style scoped>
.public-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  color: #fff;
}
</style>