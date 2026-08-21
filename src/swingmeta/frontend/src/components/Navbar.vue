<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Users, Music, Settings, Disc3, Sparkles, ListMusic } from 'lucide-vue-next';
import { api } from '../api/client';
import type { SystemStatus } from '../types';

const router = useRouter();
const route = useRoute();
const status = ref<SystemStatus | null>(null);

onMounted(async () => {
  try {
    status.value = await api.getSystemStatus();
  } catch (e) {
    console.warn('Backend offline ou inacessível');
  }
});
</script>

<template>
  <header class="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-white/5">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-center space-x-3 cursor-pointer" @click="router.push('/')">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-accent to-emerald-400 flex items-center justify-center shadow-lg shadow-accent/20">
          <Disc3 class="w-6 h-6 text-black animate-spin-slow" />
        </div>
        <div>
          <div class="flex items-center space-x-1.5">
            <span class="font-bold text-lg text-white tracking-tight">Swing<span class="text-accent">Meta</span></span>
            <span class="px-1.5 py-0.5 text-[10px] font-medium bg-accent/10 text-accent rounded border border-accent/20">Side-load</span>
          </div>
          <p class="text-[11px] text-gray-400">Gerenciador de Metadados & Fotos</p>
        </div>
      </div>

      <!-- Navigation links -->
      <nav class="flex items-center space-x-1 sm:space-x-2">
        <router-link
          to="/"
          class="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all"
          :class="route.path === '/' || route.name === 'artist-detail' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'"
        >
          <Users class="w-4 h-4" />
          <span>Artistas</span>
        </router-link>

        <router-link
          to="/tracks"
          class="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all"
          :class="route.path.startsWith('/tracks') ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'"
        >
          <Music class="w-4 h-4" />
          <span>Músicas</span>
        </router-link>

        <router-link
          to="/playlists"
          class="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all"
          :class="route.path.startsWith('/playlists') ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'"
        >
          <ListMusic class="w-4 h-4" />
          <span>Playlists</span>
        </router-link>

        <router-link
          to="/swingmusic"
          class="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all"
          :class="route.path.startsWith('/swingmusic') ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'"
        >
          <Sparkles class="w-4 h-4 text-accent" />
          <span>SwingMusic</span>
        </router-link>

        <router-link
          to="/settings"
          class="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all"
          :class="route.path === '/settings' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'"
        >
          <Settings class="w-4 h-4" />
          <span>Configurações</span>
        </router-link>
      </nav>

      <!-- Status Indicator -->
      <div class="hidden md:flex items-center space-x-3 text-xs">
        <div v-if="status" class="flex items-center space-x-2 px-2.5 py-1 rounded-full bg-surface-elevated border border-white/5">
          <span
            class="w-2 h-2 rounded-full animate-pulse"
            :class="status.mounts.swingmusic_db_exists ? 'bg-accent' : 'bg-amber-400'"
          ></span>
          <span class="text-gray-300">
            {{ status.stats.track_count }} faixas • {{ status.stats.artist_image_count }} fotos
          </span>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 20s linear infinite;
}
</style>
