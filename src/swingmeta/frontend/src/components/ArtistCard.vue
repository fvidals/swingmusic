<script setup lang="ts">
import { computed } from 'vue';
import { User, Image as ImageIcon, FileText, CheckCircle2, AlertCircle } from 'lucide-vue-next';
import type { Artist } from '../types';

const props = defineProps<{
  artist: Artist;
}>();

const emit = defineEmits<{
  (e: 'select', artist: Artist): void;
}>();

const dominantColor = computed(() => {
  if (props.artist.colors && props.artist.colors.length > 0) {
    return props.artist.colors[0];
  }
  return 'rgba(30, 30, 30, 0.6)';
});
</script>

<template>
  <div
    @click="emit('select', artist)"
    class="group relative bg-surface rounded-2xl p-4 border border-white/5 hover:border-white/20 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 cursor-pointer flex flex-col items-center text-center overflow-hidden"
  >
    <!-- Dynamic glow overlay based on artist dominant color -->
    <div
      class="absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-0 group-hover:opacity-30 transition-opacity duration-500 pointer-events-none"
      :style="{ background: dominantColor }"
    ></div>

    <!-- Avatar -->
    <div class="relative w-28 h-28 sm:w-32 sm:h-32 mb-3.5 rounded-full overflow-hidden shadow-lg bg-surface-elevated flex items-center justify-center ring-2 ring-white/10 group-hover:ring-accent/50 transition-all">
      <img
        v-if="artist.has_image && artist.image"
        :src="artist.image"
        :alt="artist.name"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center bg-surface-hover text-gray-400">
        <User class="w-12 h-12 text-gray-500" />
      </div>

      <!-- Image Status Badge -->
      <div
        class="absolute bottom-1 right-1 p-1 rounded-full text-xs shadow-md"
        :class="artist.has_image ? 'bg-emerald-500/90 text-white' : 'bg-amber-500/90 text-black'"
        :title="artist.has_image ? 'Foto presente' : 'Sem foto'"
      >
        <CheckCircle2 v-if="artist.has_image" class="w-3.5 h-3.5" />
        <AlertCircle v-else class="w-3.5 h-3.5" />
      </div>
    </div>

    <!-- Artist Name -->
    <h3 class="font-semibold text-base text-gray-100 group-hover:text-white truncate w-full px-1">
      {{ artist.name }}
    </h3>

    <!-- Stats -->
    <p class="text-xs text-gray-400 mt-1 flex items-center space-x-1.5">
      <span>{{ artist.album_count }} {{ artist.album_count === 1 ? 'álbum' : 'álbuns' }}</span>
      <span>•</span>
      <span>{{ artist.track_count }} {{ artist.track_count === 1 ? 'música' : 'músicas' }}</span>
    </p>

    <!-- Bio & Extras Indicator -->
    <div class="mt-3 flex items-center space-x-1.5 text-[11px]">
      <span
        v-if="artist.has_bio"
        class="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center space-x-1"
      >
        <FileText class="w-3 h-3" />
        <span>Bio</span>
      </span>
      <span
        v-if="!artist.has_image"
        class="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20"
      >
        Precisa de foto
      </span>
    </div>
  </div>
</template>
