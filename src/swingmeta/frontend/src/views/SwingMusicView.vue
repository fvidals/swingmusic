<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  Sparkles,
  Users,
  Image as ImageIcon,
  Globe,
  Upload,
  Trash2,
  Check,
  AlertCircle,
  Loader2,
  Shield,
  User as UserIcon,
  RefreshCw,
  Edit2,
  FileCode,
  FolderTree,
} from 'lucide-vue-next';
import { api } from '../api/client';
import type { SwingUser, FallbackAsset, ClientInfo } from '../types';

const activeTab = ref<'users' | 'assets' | 'client'>('users');

// Users state
const users = ref<SwingUser[]>([]);
const isUsersLoading = ref(true);
const uploadingUserId = ref<number | null>(null);

// Fallback assets state
const assets = ref<FallbackAsset[]>([]);
const isAssetsLoading = ref(true);
const uploadingAssetName = ref<string | null>(null);

// WebClient state
const clientInfo = ref<ClientInfo | null>(null);
const isClientLoading = ref(true);

const feedbackMsg = ref('');
const errorMsg = ref('');

// User edit modal
const editingUser = ref<SwingUser | null>(null);
const editUsername = ref('');
const editFirstname = ref('');
const editEmail = ref('');
const isSavingUser = ref(false);

async function loadUsers() {
  isUsersLoading.value = true;
  try {
    const res = await api.getSwingUsers();
    users.value = res.users || [];
  } catch (err: any) {
    console.warn('Erro ao carregar usuários:', err);
  } finally {
    isUsersLoading.value = false;
  }
}

async function loadAssets() {
  isAssetsLoading.value = true;
  try {
    const res = await api.getFallbackAssets();
    assets.value = res.assets || [];
  } catch (err: any) {
    console.warn('Erro ao carregar assets:', err);
  } finally {
    isAssetsLoading.value = false;
  }
}

async function loadClientInfo() {
  isClientLoading.value = true;
  try {
    clientInfo.value = await api.getClientInfo();
  } catch (err: any) {
    console.warn('Erro ao carregar info do client:', err);
  } finally {
    isClientLoading.value = false;
  }
}

function showSuccess(msg: string) {
  feedbackMsg.value = msg;
  errorMsg.value = '';
  setTimeout(() => {
    feedbackMsg.value = '';
  }, 4000);
}

function showError(msg: string) {
  errorMsg.value = msg;
  feedbackMsg.value = '';
}

// User Avatar Upload
async function onUserAvatarSelected(userId: number, event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target.files || target.files.length === 0) return;

  const file = target.files[0];
  uploadingUserId.value = userId;
  errorMsg.value = '';

  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const base64 = reader.result as string;
      const res = await api.uploadUserAvatar(userId, base64);
      showSuccess(`Foto do usuário atualizada com sucesso!`);
      // Update local user
      const user = users.value.find(u => u.id === userId);
      if (user) {
        user.avatar_url = `${res.avatar_url}?t=${Date.now()}`;
        user.has_custom_avatar = true;
      }
    } catch (err: any) {
      showError(err.message || 'Erro ao enviar foto');
    } finally {
      uploadingUserId.value = null;
      target.value = '';
    }
  };
  reader.readAsDataURL(file);
}

async function deleteAvatar(user: SwingUser) {
  if (!confirm(`Deseja remover a foto customizada do usuário ${user.username}?`)) return;
  try {
    await api.deleteUserAvatar(user.id);
    user.avatar_url = null;
    user.has_custom_avatar = false;
    showSuccess(`Foto do usuário ${user.username} removida.`);
  } catch (err: any) {
    showError(err.message || 'Erro ao remover foto');
  }
}

function openEditModal(user: SwingUser) {
  editingUser.value = user;
  editUsername.value = user.username;
  editFirstname.value = user.firstname || '';
  editEmail.value = user.email || '';
}

async function saveUserEdit() {
  if (!editingUser.value) return;
  isSavingUser.value = true;
  try {
    await api.updateSwingUser(editingUser.value.id, {
      username: editUsername.value,
      extra: {
        firstname: editFirstname.value,
        email: editEmail.value,
      },
    });
    editingUser.value.username = editUsername.value;
    editingUser.value.firstname = editFirstname.value;
    editingUser.value.email = editEmail.value;
    showSuccess(`Dados do usuário ${editUsername.value} salvos com sucesso!`);
    editingUser.value = null;
  } catch (err: any) {
    showError(err.message || 'Erro ao salvar usuário');
  } finally {
    isSavingUser.value = false;
  }
}

// Fallback Asset Upload
async function onAssetSelected(assetName: string, event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target.files || target.files.length === 0) return;

  const file = target.files[0];
  uploadingAssetName.value = assetName;

  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const base64 = reader.result as string;
      await api.uploadFallbackAsset(assetName, base64);
      showSuccess(`Asset "${assetName}" atualizado com sucesso no SwingMusic!`);
      loadAssets();
    } catch (err: any) {
      showError(err.message || 'Erro ao substituir asset');
    } finally {
      uploadingAssetName.value = null;
      target.value = '';
    }
  };
  reader.readAsDataURL(file);
}

onMounted(() => {
  loadUsers();
  loadAssets();
  loadClientInfo();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header Hero -->
    <div class="bg-gradient-to-b from-surface-elevated/80 to-surface rounded-3xl p-6 sm:p-8 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center space-x-2 text-accent text-sm font-medium mb-1">
          <Sparkles class="w-4 h-4" />
          <span>Personalização do SwingMusic</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Usuários, Avatares & Identidade Visual
        </h1>
        <p class="text-sm text-gray-400 mt-1">
          Gerencie fotos de perfil dos usuários do SwingMusic, substitua assets padrão (artistas e capas sem foto) e visualize a pasta do WebClient.
        </p>
      </div>

      <!-- Tab selectors -->
      <div class="flex items-center bg-surface-elevated p-1 rounded-2xl border border-white/5 text-xs self-start md:self-auto">
        <button
          @click="activeTab = 'users'"
          class="px-4 py-2 rounded-xl font-medium transition-all flex items-center space-x-1.5"
          :class="activeTab === 'users' ? 'bg-accent text-black font-bold shadow' : 'text-gray-400 hover:text-white'"
        >
          <Users class="w-3.5 h-3.5" />
          <span>Usuários ({{ users.length }})</span>
        </button>

        <button
          @click="activeTab = 'assets'"
          class="px-4 py-2 rounded-xl font-medium transition-all flex items-center space-x-1.5"
          :class="activeTab === 'assets' ? 'bg-accent text-black font-bold shadow' : 'text-gray-400 hover:text-white'"
        >
          <ImageIcon class="w-3.5 h-3.5" />
          <span>Assets Padrão</span>
        </button>

        <button
          @click="activeTab = 'client'"
          class="px-4 py-2 rounded-xl font-medium transition-all flex items-center space-x-1.5"
          :class="activeTab === 'client' ? 'bg-accent text-black font-bold shadow' : 'text-gray-400 hover:text-white'"
        >
          <Globe class="w-3.5 h-3.5" />
          <span>WebClient</span>
        </button>
      </div>
    </div>

    <!-- Alert Feedback -->
    <div v-if="feedbackMsg" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-2xl text-xs flex items-center space-x-2 shadow-lg">
      <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
      <span>{{ feedbackMsg }}</span>
    </div>

    <div v-if="errorMsg" class="p-4 bg-red-500/10 border border-red-500/20 text-red-300 rounded-2xl text-xs flex items-center space-x-2">
      <AlertCircle class="w-4 h-4 text-red-400 flex-shrink-0" />
      <span>{{ errorMsg }}</span>
    </div>

    <!-- TAB 1: USERS & AVATARS -->
    <div v-if="activeTab === 'users'" class="space-y-4">
      <div v-if="isUsersLoading" class="py-24 flex flex-col items-center justify-center space-y-3 text-gray-400">
        <Loader2 class="w-8 h-8 animate-spin text-accent" />
        <p class="text-sm">Carregando usuários do SwingMusic...</p>
      </div>

      <div v-else-if="users.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="u in users"
          :key="u.id"
          class="bg-surface rounded-3xl p-6 border border-white/5 hover:border-white/15 transition-all flex flex-col justify-between shadow-lg relative overflow-hidden group"
        >
          <!-- Top info & Avatar -->
          <div class="flex items-start space-x-4">
            <!-- Avatar with Hover Upload overlay -->
            <div class="relative group/avatar">
              <div class="w-18 h-18 rounded-full overflow-hidden bg-surface-elevated border-2 border-white/10 flex items-center justify-center flex-shrink-0 shadow-md">
                <img
                  v-if="u.avatar_url"
                  :src="u.avatar_url"
                  :alt="u.username"
                  class="w-full h-full object-cover"
                />
                <UserIcon v-else class="w-8 h-8 text-gray-500" />
              </div>

              <!-- Upload input overlay -->
              <label
                class="absolute inset-0 rounded-full bg-black/60 opacity-0 group-hover/avatar:opacity-100 flex flex-col items-center justify-center cursor-pointer transition-all text-white text-[10px] font-semibold"
                :title="'Alterar foto de ' + u.username"
              >
                <Upload class="w-4 h-4 mb-0.5 text-accent" />
                <span>Trocar</span>
                <input
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="onUserAvatarSelected(u.id, $event)"
                />
              </label>

              <!-- Loading spinner -->
              <div
                v-if="uploadingUserId === u.id"
                class="absolute inset-0 rounded-full bg-black/80 flex items-center justify-center"
              >
                <Loader2 class="w-5 h-5 text-accent animate-spin" />
              </div>
            </div>

            <!-- Details -->
            <div class="min-w-0 flex-1">
              <div class="flex items-center space-x-2">
                <h3 class="text-base font-bold text-white truncate">{{ u.username }}</h3>
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center space-x-1"
                  :class="u.is_admin ? 'bg-accent/10 text-accent border border-accent/20' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'"
                >
                  <Shield v-if="u.is_admin" class="w-2.5 h-2.5" />
                  <span>{{ u.roles.join(', ') || 'user' }}</span>
                </span>
              </div>

              <p v-if="u.firstname" class="text-xs text-gray-300 mt-0.5">{{ u.firstname }}</p>
              <p v-if="u.email" class="text-xs text-gray-500 mt-0.5 truncate">{{ u.email }}</p>
              <p class="text-[11px] text-gray-600 font-mono mt-1">ID: #{{ u.id }}</p>
            </div>
          </div>

          <!-- Bottom Actions -->
          <div class="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-xs">
            <label class="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white rounded-xl cursor-pointer transition-all flex items-center space-x-1.5 font-medium">
              <Upload class="w-3.5 h-3.5 text-accent" />
              <span>Upload Foto</span>
              <input
                type="file"
                accept="image/*"
                class="hidden"
                @change="onUserAvatarSelected(u.id, $event)"
              />
            </label>

            <div class="flex items-center space-x-1">
              <button
                @click="openEditModal(u)"
                class="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition-all"
                title="Editar informações"
              >
                <Edit2 class="w-3.5 h-3.5" />
              </button>

              <button
                v-if="u.has_custom_avatar"
                @click="deleteAvatar(u)"
                class="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all"
                title="Remover foto customizada"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="py-20 text-center bg-surface rounded-3xl border border-white/5 space-y-3">
        <Users class="w-12 h-12 text-gray-600 mx-auto mb-2" />
        <h3 class="text-lg font-medium text-gray-300">Nenhum usuário encontrado em userdata.db</h3>
      </div>
    </div>

    <!-- TAB 2: FALLBACK ASSETS -->
    <div v-else-if="activeTab === 'assets'" class="space-y-4">
      <div class="bg-surface rounded-2xl p-5 border border-white/5 text-xs text-gray-400 flex items-start space-x-3">
        <ImageIcon class="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
        <div>
          <strong class="text-white font-medium">Imagens Padrão de Fallback:</strong>
          <p class="mt-0.5">
            Essas imagens são exibidas pelo SwingMusic quando um artista não possui foto ou um álbum/playlist não possui capa. Você pode substituí-las por suas próprias artes ou logos personalizados.
          </p>
        </div>
      </div>

      <div v-if="isAssetsLoading" class="py-20 flex justify-center text-accent">
        <Loader2 class="w-8 h-8 animate-spin" />
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="a in assets"
          :key="a.name"
          class="bg-surface rounded-3xl p-5 border border-white/5 flex flex-col justify-between space-y-4 shadow-sm"
        >
          <!-- Asset Preview -->
          <div>
            <div class="w-full aspect-square rounded-2xl bg-surface-elevated border border-white/5 flex items-center justify-center overflow-hidden relative group">
              <img
                v-if="a.url"
                :src="a.url"
                :alt="a.name"
                class="w-full h-full object-contain p-4"
              />
              <ImageIcon v-else class="w-12 h-12 text-gray-600" />

              <!-- Overlay Upload -->
              <label class="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center cursor-pointer transition-all text-white text-xs font-semibold">
                <Upload class="w-6 h-6 text-accent mb-1" />
                <span>Substituir</span>
                <input
                  type="file"
                  :accept="a.name.endsWith('.svg') ? '.svg' : 'image/*'"
                  class="hidden"
                  @change="onAssetSelected(a.name, $event)"
                />
              </label>

              <div v-if="uploadingAssetName === a.name" class="absolute inset-0 bg-black/80 flex items-center justify-center">
                <Loader2 class="w-6 h-6 text-accent animate-spin" />
              </div>
            </div>

            <!-- Asset info -->
            <div class="mt-3">
              <h4 class="font-bold text-sm text-white">{{ a.label }}</h4>
              <p class="text-[11px] text-gray-400 font-mono mt-0.5">{{ a.name }}</p>
              <p class="text-[11px] text-gray-500 mt-1">
                {{ a.exists ? `${(a.size_bytes / 1024).toFixed(1)} KB` : 'Não customizado' }}
              </p>
            </div>
          </div>

          <!-- Bottom Button -->
          <label class="w-full py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-semibold rounded-xl border border-white/10 flex items-center justify-center space-x-1.5 cursor-pointer transition-all">
            <Upload class="w-3.5 h-3.5 text-accent" />
            <span>Enviar Novo {{ a.name.endsWith('.svg') ? 'SVG' : 'WebP' }}</span>
            <input
              type="file"
              :accept="a.name.endsWith('.svg') ? '.svg' : 'image/*'"
              class="hidden"
              @change="onAssetSelected(a.name, $event)"
            />
          </label>
        </div>
      </div>
    </div>

    <!-- TAB 3: WEBCLIENT INFO -->
    <div v-else-if="activeTab === 'client'" class="space-y-4">
      <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-6 shadow-sm">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
            <Globe class="w-6 h-6" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white">Client Web do SwingMusic</h2>
            <p class="text-xs text-gray-400">
              Arquivos de interface SPA extraídos no diretório de configuração do contêiner.
            </p>
          </div>
        </div>

        <div v-if="clientInfo" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
            <span class="text-xs text-gray-400">Status do Client</span>
            <p class="text-sm font-bold mt-1 flex items-center space-x-1.5" :class="clientInfo.exists ? 'text-emerald-400' : 'text-amber-400'">
              <Check v-if="clientInfo.exists" class="w-4 h-4" />
              <AlertCircle v-else class="w-4 h-4" />
              <span>{{ clientInfo.exists ? 'Instalado & Extraído' : 'Não encontrado' }}</span>
            </p>
          </div>

          <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
            <span class="text-xs text-gray-400">Versão do WebClient</span>
            <p class="text-sm font-bold text-white mt-1 font-mono">
              {{ clientInfo.version }}
            </p>
          </div>

          <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
            <span class="text-xs text-gray-400">Arquivos Totais</span>
            <p class="text-sm font-bold text-white mt-1">
              {{ clientInfo.total_files }} arquivos
            </p>
          </div>
        </div>

        <div v-if="clientInfo" class="p-4 bg-surface-elevated/50 rounded-2xl border border-white/5 space-y-2 text-xs">
          <div class="flex items-center space-x-2 text-gray-300 font-mono">
            <FolderTree class="w-4 h-4 text-accent flex-shrink-0" />
            <span>Caminho no volume: <strong class="text-white">{{ clientInfo.path }}</strong></span>
          </div>
          <p class="text-gray-500">
            Você pode customizar estilos, ícones ou scripts adicionais diretamente montando ou editando este diretório no seu servidor.
          </p>
        </div>
      </div>
    </div>

    <!-- Edit User Modal -->
    <div v-if="editingUser" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div class="bg-surface rounded-3xl border border-white/10 w-full max-w-md p-6 space-y-5 shadow-2xl">
        <h3 class="text-base font-bold text-white">Editar Usuário: {{ editingUser.username }}</h3>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block text-gray-400 mb-1 font-medium">Nome de Usuário (Username)</label>
            <input
              v-model="editUsername"
              type="text"
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label class="block text-gray-400 mb-1 font-medium">Primeiro Nome</label>
            <input
              v-model="editFirstname"
              type="text"
              placeholder="Ex: João"
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label class="block text-gray-400 mb-1 font-medium">Email</label>
            <input
              v-model="editEmail"
              type="email"
              placeholder="usuario@exemplo.com"
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2">
          <button
            @click="editingUser = null"
            class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-xl transition-all"
          >
            Cancelar
          </button>
          <button
            @click="saveUserEdit"
            :disabled="isSavingUser"
            class="px-5 py-2 bg-accent text-black text-xs font-bold rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5 shadow-lg shadow-accent/20"
          >
            <Loader2 v-if="isSavingUser" class="w-3.5 h-3.5 animate-spin" />
            <span>{{ isSavingUser ? 'Salvando...' : 'Salvar Alterações' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
