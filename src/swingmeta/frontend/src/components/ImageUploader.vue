<script setup lang="ts">
import { ref } from 'vue';
import { UploadCloud, Link as LinkIcon, Check, Loader2, Trash2 } from 'lucide-vue-next';
import { api } from '../api/client';

const props = defineProps<{
  artisthash: string;
  currentImage?: string | null;
}>();

const emit = defineEmits<{
  (e: 'uploaded', result: any): void;
  (e: 'deleted'): void;
}>();

const isDragging = ref(false);
const isLoading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const showUrlInput = ref(false);
const directUrl = ref('');
const fileInput = ref<HTMLInputElement | null>(null);

async function handleFile(file: File) {
  if (!file.type.startsWith('image/')) {
    errorMsg.value = 'Por favor, selecione um arquivo de imagem válido (JPG, PNG, WebP).';
    return;
  }

  errorMsg.value = '';
  successMsg.value = '';
  isLoading.value = true;

  try {
    const result = await api.uploadArtistImageFile(props.artisthash, file);
    successMsg.value = 'Foto atualizada e convertida para WebP com sucesso!';
    emit('uploaded', result);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao enviar a imagem.';
  } finally {
    isLoading.value = false;
  }
}

function onDrop(e: DragEvent) {
  isDragging.value = false;
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    handleFile(e.dataTransfer.files[0]);
  }
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    handleFile(target.files[0]);
  }
}

async function submitUrl() {
  if (!directUrl.value.trim()) return;

  errorMsg.value = '';
  successMsg.value = '';
  isLoading.value = true;

  try {
    const result = await api.applyOnlineImage(props.artisthash, directUrl.value.trim());
    successMsg.value = 'Imagem baixada e aplicada com sucesso!';
    directUrl.value = '';
    showUrlInput.value = false;
    emit('uploaded', result);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao baixar imagem da URL.';
  } finally {
    isLoading.value = false;
  }
}

async function removeImage() {
  if (!confirm('Deseja realmente remover a foto customizada deste artista?')) return;
  isLoading.value = true;
  try {
    await api.deleteArtistImage(props.artisthash);
    successMsg.value = 'Foto removida.';
    emit('deleted');
  } catch (err: any) {
    errorMsg.value = 'Erro ao remover foto.';
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Drag and drop container -->
    <div
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInput?.click()"
      class="relative border-2 border-dashed rounded-2xl p-6 sm:p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200"
      :class="isDragging ? 'border-accent bg-accent/10 scale-[1.01]' : 'border-white/10 hover:border-white/30 bg-surface-elevated/50'"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="onFileSelect"
      />

      <div v-if="isLoading" class="flex flex-col items-center space-y-2 py-4">
        <Loader2 class="w-8 h-8 text-accent animate-spin" />
        <span class="text-sm text-gray-300">Processando e gerando WebP...</span>
      </div>

      <div v-else class="flex flex-col items-center space-y-2">
        <div class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-accent mb-1">
          <UploadCloud class="w-6 h-6" />
        </div>
        <p class="text-sm font-medium text-gray-200">
          Arraste uma nova foto aqui ou <span class="text-accent underline">clique para selecionar</span>
        </p>
        <p class="text-xs text-gray-400">
          Suporta JPG, PNG, WEBP. A imagem será recortada 1:1 e redimensionada automaticamente.
        </p>
      </div>
    </div>

    <!-- URL Input toggle -->
    <div class="flex items-center justify-between text-xs text-gray-400 px-1">
      <button
        @click="showUrlInput = !showUrlInput"
        class="flex items-center space-x-1.5 hover:text-white transition-colors"
      >
        <LinkIcon class="w-3.5 h-3.5" />
        <span>{{ showUrlInput ? 'Ocultar campo de URL' : 'Enviar por link direto de imagem' }}</span>
      </button>

      <button
        v-if="currentImage"
        @click="removeImage"
        class="flex items-center space-x-1 text-red-400 hover:text-red-300 transition-colors"
      >
        <Trash2 class="w-3.5 h-3.5" />
        <span>Remover foto</span>
      </button>
    </div>

    <!-- Direct URL Form -->
    <div v-if="showUrlInput" class="flex space-x-2">
      <input
        v-model="directUrl"
        type="url"
        placeholder="https://exemplo.com/foto-artista.jpg"
        class="flex-1 bg-surface-elevated border border-white/10 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-accent"
        @keyup.enter="submitUrl"
      />
      <button
        @click="submitUrl"
        :disabled="isLoading || !directUrl"
        class="px-4 py-2 bg-accent text-black font-medium text-sm rounded-lg hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1"
      >
        <Check class="w-4 h-4" />
        <span>Aplicar</span>
      </button>
    </div>

    <!-- Alerts -->
    <div v-if="errorMsg" class="p-3 bg-red-500/10 border border-red-500/20 text-red-300 rounded-lg text-xs">
      {{ errorMsg }}
    </div>
    <div v-if="successMsg" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-lg text-xs">
      {{ successMsg }}
    </div>
  </div>
</template>
