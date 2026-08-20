<script setup lang="ts">
import Navbar from './components/Navbar.vue';
</script>

<template>
  <div class="min-h-screen bg-background text-gray-100 flex flex-col">
    <!-- Top Navigation Bar -->
    <Navbar />

    <!-- Main Content View -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Simple Footer -->
    <footer class="border-t border-white/5 py-6 text-center text-xs text-gray-500">
      <p>SwingMeta • Companheiro de Metadados para o SwingMusic</p>
    </footer>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
