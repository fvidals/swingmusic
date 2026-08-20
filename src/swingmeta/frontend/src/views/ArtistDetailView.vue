<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowLeft,
  Sparkles,
  Upload,
  User,
  Disc,
  Music,
  CheckCircle2,
  AlertCircle,
  Clock,
  Edit3,
  Loader2,
} from 'lucide-vue-next';
import { api } from '../api/client';
import type { ArtistDetail, Track } from '../types';
import ImageUploader from '../components/ImageUploader.vue';
import OnlineSearchModal from '../components/OnlineSearchModal.vue';
import BioEditor from '../components/BioEditor.vue';
import TagEditorModal from '../components/TagEditorModal.vue';

const route = useRoute();
const router = useRouter();

const artisthash = ref(route.params.artisthash as string);
const artist = ref<ArtistDetail | null>(null);
const isLoading = ref(true);
const errorMsg = ref('');

const showOnlineModal = ref(false);
const activeTab = ref<'albums' | 'tracks' | 'upload' | 'bio'>('upload');
const selectedTrackForTagEdit = ref<Track | null>(null);

const dominantColor = computed(() => {
  if (artist.value?.colors && artist.value.colors.length > 0) {
    return artist.value.colors[0];
  }
  return '#1e1e1e';
});

async function loadArtist() {
  isLoading.value = true;
  errorMsg.value = '';
  try {
    artist.value = await api.getArtist(artisthash.value);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao carregar artista';
  } finally {
    isLoading.value = false;
  }
}

function handleImageUploaded(result: any) {
  loadArtist();
}

function handleImageDeleted() {
  loadArtist();
}

function handleBioSaved(newBio: string) {
  if (artist.value) {
    artist.value.bio = newBio;
    artist.value.has_bio = Boolean(newBio.trim());
  }
}

function openTagEditor(track: Track) {
  selectedTrackForTagEdit.value = track;
}

function handleTagsUpdated(newTags: any) {
  loadArtist();
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

onMounted(() => {
  loadArtist();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Back Button -->
    <button
      @click="router.push('/')"
      class="flex items-center space-x-2 text-sm text-gray-400 hover:text-white transition-colors group"
    >
      <ArrowLeft class="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
      <span>Voltar para lista de artistas</span>
    </button>

    <div v-if="isLoading" class="py-32 flex flex-col items-center justify-center space-y-3 text-gray-400">
      <Loader2 class="w-10 h-10 animate-spin text-accent" />
      <p class="text-sm">Carregando dados do artista...</p>
    </div>

    <div v-else-if="errorMsg" class="p-8 bg-surface rounded-3xl border border-red-500/20 text-center">
      <AlertCircle class="w-12 h-12 text-red-400 mx-auto mb-3" />
      <h2 class="text-lg font-semibold text-white">{{ errorMsg }}</h2>
      <button
        @click="router.push('/')"
        class="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm rounded-xl"
      >
        Ir para Artistas
      </button>
    </div>

    <template v-else-if="artist">
      <!-- Hero Banner with dominant color gradient -->
      <div
        class="relative rounded-3xl overflow-hidden p-6 sm:p-10 border border-white/10 shadow-2xl flex flex-col md:flex-row items-center md:items-end gap-6 sm:gap-8"
        :style="{
          background: `linear-gradient(135deg, ${dominantColor}55 0%, #181818 100%)`
        }"
      >
        <!-- Circle Avatar with click to upload -->
        <div class="relative group w-36 h-36 sm:w-44 sm:h-44 rounded-full overflow-hidden shadow-2xl ring-4 ring-white/10 flex-shrink-0 bg-surface">
          <img
            v-if="artist.has_image && artist.image_lg"
            :src="artist.image_lg"
            :alt="artist.name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center bg-surface-elevated text-gray-400">
            <User class="w-20 h-20 text-gray-500" />
          </div>

          <!-- Overlay trigger for upload -->
          <div
            @click="activeTab = 'upload'"
            class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white cursor-pointer"
          >
            <Upload class="w-6 h-6 mb-1 text-accent" />
            <span class="text-xs font-semibold">Alterar Foto</span>
          </div>
        </div>

        <!-- Artist Information -->
        <div class="flex-1 text-center md:text-left space-y-2">
          <div class="flex flex-wrap items-center justify-center md:justify-start gap-2">
            <span
              class="px-2.5 py-0.5 rounded-full text-xs font-medium border"
              :class="artist.has_image ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border-amber-500/20'"
            >
              {{ artist.has_image ? 'Foto Configurada' : 'Sem Imagem' }}
            </span>
            <span
              v-if="artist.has_bio"
              class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20"
            >
              Biografia Presente
            </span>
          </div>

          <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight">
            {{ artist.name }}
          </h1>

          <div class="flex flex-wrap items-center justify-center md:justify-start gap-3 text-xs sm:text-sm text-gray-300">
            <span>{{ artist.album_count }} {{ artist.album_count === 1 ? 'álbum' : 'álbuns' }}</span>
            <span>•</span>
            <span>{{ artist.track_count }} {{ artist.track_count === 1 ? 'música' : 'músicas' }}</span>
            <span>•</span>
            <span>Hash: <code class="font-mono text-gray-400">{{ artist.artisthash }}</code></span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
          <button
            @click="showOnlineModal = true"
            class="px-5 py-3 bg-accent text-black font-bold text-sm rounded-2xl hover:bg-accent/90 transition-all flex items-center justify-center space-x-2 shadow-lg shadow-accent/25"
          >
            <Sparkles class="w-4 h-4" />
            <span>Buscar Foto Online</span>
          </button>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex border-b border-white/10 space-x-4 sm:space-x-8 text-sm font-medium">
        <button
          @click="activeTab = 'upload'"
          class="pb-3 flex items-center space-x-2 transition-all relative"
          :class="activeTab === 'upload' ? 'text-accent font-semibold' : 'text-gray-400 hover:text-white'"
        >
          <Upload class="w-4 h-4" />
          <span>Upload de Imagem</span>
          <span v-if="activeTab === 'upload'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"></span>
        </button>

        <button
          @click="activeTab = 'bio'"
          class="pb-3 flex items-center space-x-2 transition-all relative"
          :class="activeTab === 'bio' ? 'text-accent font-semibold' : 'text-gray-400 hover:text-white'"
        >
          <Edit3 class="w-4 h-4" />
          <span>Biografia</span>
          <span v-if="activeTab === 'bio'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"></span>
        </button>

        <button
          @click="activeTab = 'albums'"
          class="pb-3 flex items-center space-x-2 transition-all relative"
          :class="activeTab === 'albums' ? 'text-accent font-semibold' : 'text-gray-400 hover:text-white'"
        >
          <Disc class="w-4 h-4" />
          <span>Álbuns ({{ artist.albums.length }})</span>
          <span v-if="activeTab === 'albums'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"></span>
        </button>

        <button
          @click="activeTab = 'tracks'"
          class="pb-3 flex items-center space-x-2 transition-all relative"
          :class="activeTab === 'tracks' ? 'text-accent font-semibold' : 'text-gray-400 hover:text-white'"
        >
          <Music class="w-4 h-4" />
          <span>Músicas & Tags ({{ artist.tracks.length }})</span>
          <span v-if="activeTab === 'tracks'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"></span>
        </button>
      </div>

      <!-- Tab Content Area -->
      <div>
        <!-- Upload Tab -->
        <div v-if="activeTab === 'upload'" class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-bold text-white">Upload de Foto Customizada</h2>
              <p class="text-xs text-gray-400 mt-0.5">
                O arquivo será processado para WebP nas 3 resoluções e vinculado ao hash do SwingMusic.
              </p>
            </div>
            <button
              @click="showOnlineModal = true"
              class="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-semibold rounded-xl border border-white/10 flex items-center space-x-1.5 transition-all"
            >
              <Sparkles class="w-3.5 h-3.5 text-accent" />
              <span>Usar busca online (Deezer/Spotify)</span>
            </button>
          </div>

          <ImageUploader
            :artisthash="artist.artisthash"
            :current-image="artist.image"
            @uploaded="handleImageUploaded"
            @deleted="handleImageDeleted"
          />
        </div>

        <!-- Bio Tab -->
        <div v-if="activeTab === 'bio'">
          <BioEditor
            :artisthash="artist.artisthash"
            :initial-bio="artist.bio"
            @saved="handleBioSaved"
          />
        </div>

        <!-- Albums Tab -->
        <div v-if="activeTab === 'albums'" class="space-y-4">
          <div v-if="artist.albums.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div
              v-for="album in artist.albums"
              :key="album.albumhash"
              class="bg-surface rounded-2xl p-4 border border-white/5 flex flex-col items-center text-center space-y-2 hover:border-white/20 transition-all group"
            >
              <div class="w-28 h-28 sm:w-32 sm:h-32 rounded-xl overflow-hidden bg-surface-elevated shadow-md group-hover:scale-105 transition-transform">
                <img
                  v-if="album.cover"
                  :src="album.cover"
                  :alt="album.title"
                  class="w-full h-full object-cover"
                  loading="lazy"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-500">
                  <Disc class="w-10 h-10" />
                </div>
              </div>
              <span class="font-semibold text-sm text-white truncate w-full">{{ album.title }}</span>
              <span v-if="album.date" class="text-xs text-gray-400">{{ album.date }}</span>
            </div>
          </div>
          <div v-else class="py-12 text-center text-gray-500 bg-surface rounded-2xl">
            Nenhum álbum indexado para este artista.
          </div>
        </div>

        <!-- Tracks Tab -->
        <div v-if="activeTab === 'tracks'" class="bg-surface rounded-3xl p-6 border border-white/5 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-white">Músicas do Artista</h2>
            <span class="text-xs text-gray-400">Clique no ícone de lápis para editar tags ID3</span>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-gray-300">
              <thead class="text-xs uppercase bg-surface-elevated text-gray-400 border-b border-white/5">
                <tr>
                  <th class="px-4 py-3">#</th>
                  <th class="px-4 py-3">Título</th>
                  <th class="px-4 py-3">Álbum</th>
                  <th class="px-4 py-3"><Clock class="w-3.5 h-3.5" /></th>
                  <th class="px-4 py-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/5">
                <tr
                  v-for="(t, idx) in artist.tracks"
                  :key="t.id"
                  class="hover:bg-white/5 transition-colors group"
                >
                  <td class="px-4 py-3 text-gray-500">{{ idx + 1 }}</td>
                  <td class="px-4 py-3 font-medium text-white">{{ t.title }}</td>
                  <td class="px-4 py-3 text-gray-400">{{ t.album }}</td>
                  <td class="px-4 py-3 text-gray-400">{{ formatDuration(t.duration) }}</td>
                  <td class="px-4 py-3 text-right">
                    <button
                      @click="openTagEditor(t)"
                      class="px-3 py-1.5 bg-white/5 hover:bg-accent hover:text-black rounded-lg text-xs font-semibold transition-all inline-flex items-center space-x-1"
                    >
                      <Edit3 class="w-3.5 h-3.5" />
                      <span>Editar Tags</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>

    <!-- Modals -->
    <OnlineSearchModal
      v-if="showOnlineModal && artist"
      :artisthash="artist.artisthash"
      :artist-name="artist.name"
      @close="showOnlineModal = false"
      @selected-image="loadArtist(); showOnlineModal = false"
    />

    <TagEditorModal
      v-if="selectedTrackForTagEdit"
      :track="selectedTrackForTagEdit"
      @close="selectedTrackForTagEdit = null"
      @updated="handleTagsUpdated"
    />
  </div>
</template>
