import type { Artist, ArtistDetail, FileTags, OnlineImageCandidate, SystemStatus, Track } from '../types';

const BASE_URL = '/api';

export const api = {
  // Artists
  async getArtists(params: {
    q?: string;
    filter?: string;
    sort?: string;
    order?: string;
    page?: number;
    limit?: number;
  }): Promise<{ total: number; page: number; limit: number; total_pages: number; artists: Artist[] }> {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.filter) query.append('filter', params.filter);
    if (params.sort) query.append('sort', params.sort);
    if (params.order) query.append('order', params.order);
    if (params.page) query.append('page', params.page.toString());
    if (params.limit) query.append('limit', params.limit.toString());

    const res = await fetch(`${BASE_URL}/artists?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao carregar artistas');
    return res.json();
  },

  async getArtist(artisthash: string): Promise<ArtistDetail> {
    const res = await fetch(`${BASE_URL}/artists/${artisthash}`);
    if (!res.ok) throw new Error('Artista não encontrado');
    return res.json();
  },

  async uploadArtistImageFile(artisthash: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/artists/${artisthash}/image`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao enviar imagem');
    }
    return res.json();
  },

  async applyOnlineImage(artisthash: string, imageUrl: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/artists/${artisthash}/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao aplicar imagem online');
    }
    return res.json();
  },

  async deleteArtistImage(artisthash: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/artists/${artisthash}/image`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Erro ao remover imagem');
    return res.json();
  },

  async searchOnline(artisthash: string, name?: string): Promise<{
    query: string;
    images: OnlineImageCandidate[];
    musicbrainz: any[];
    spotify_configured: boolean;
  }> {
    const query = name ? `?name=${encodeURIComponent(name)}` : '';
    const res = await fetch(`${BASE_URL}/artists/${artisthash}/search-online${query}`);
    if (!res.ok) throw new Error('Erro na busca online');
    return res.json();
  },

  async updateArtistMetadata(artisthash: string, data: { bio?: string; info?: any; extra?: any }): Promise<any> {
    const res = await fetch(`${BASE_URL}/artists/${artisthash}/metadata`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Erro ao salvar metadados');
    return res.json();
  },

  // Tracks & ID3 Tags
  async getTracks(params: {
    q?: string;
    artisthash?: string;
    albumhash?: string;
    filter?: string;
    page?: number;
    limit?: number;
  }): Promise<{
    total: number;
    page: number;
    limit: number;
    total_pages: number;
    counts: { total: number; has_cover: number; no_cover: number };
    tracks: Track[];
  }> {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.artisthash) query.append('artisthash', params.artisthash);
    if (params.albumhash) query.append('albumhash', params.albumhash);
    if (params.filter) query.append('filter', params.filter);
    if (params.page) query.append('page', params.page.toString());
    if (params.limit) query.append('limit', params.limit.toString());

    const res = await fetch(`${BASE_URL}/tracks?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao carregar faixas');
    return res.json();
  },

  async searchAlbumCovers(album: string, artist?: string): Promise<{
    query: string;
    covers: import('../types').OnlineAlbumCoverCandidate[];
    spotify_configured: boolean;
  }> {
    const query = new URLSearchParams({ album });
    if (artist) query.append('artist', artist);
    const res = await fetch(`${BASE_URL}/tracks/search-covers?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao buscar capas online');
    return res.json();
  },

  async uploadTrackCover(trackId: number, file: File): Promise<any> {
    const form = new FormData();
    form.append('image', file);
    const res = await fetch(`${BASE_URL}/tracks/${trackId}/cover/upload`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao enviar capa');
    }
    return res.json();
  },

  async applyTrackOnlineCover(trackId: number, imageUrl: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/tracks/${trackId}/cover/online`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao aplicar capa online');
    }
    return res.json();
  },

  async uploadAlbumCover(albumhash: string, file: File): Promise<any> {
    const form = new FormData();
    form.append('image', file);
    const res = await fetch(`${BASE_URL}/tracks/album/${albumhash}/cover/upload`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao enviar capa do álbum');
    }
    return res.json();
  },

  async applyAlbumOnlineCover(albumhash: string, imageUrl: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/tracks/album/${albumhash}/cover/online`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao aplicar capa online');
    }
    return res.json();
  },

  async applyBatchCover(
    trackIds: number[],
    options: {
      file?: File;
      imageUrl?: string;
      imageBase64?: string;
      embedAudio?: boolean;
    }
  ): Promise<{
    success: boolean;
    total_tracks: number;
    updated_files: number;
    updated_albums: number;
    albumhashes: string[];
  }> {
    const embedAudio = options.embedAudio !== false;
    let res: Response;

    if (options.file) {
      const form = new FormData();
      form.append('image', options.file);
      form.append('track_ids', JSON.stringify(trackIds));
      form.append('embed_audio', embedAudio ? 'true' : 'false');
      res = await fetch(`${BASE_URL}/tracks/batch-cover`, {
        method: 'POST',
        body: form,
      });
    } else {
      res = await fetch(`${BASE_URL}/tracks/batch-cover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track_ids: trackIds,
          image_url: options.imageUrl,
          image_base64: options.imageBase64,
          embed_audio: embedAudio,
        }),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao aplicar capa em lote');
    }
    return res.json();
  },

  async getTrackDetail(trackId: number): Promise<{ database: Track; file_tags: FileTags }> {
    const res = await fetch(`${BASE_URL}/tracks/${trackId}`);
    if (!res.ok) throw new Error('Faixa não encontrada');
    return res.json();
  },

  async updateTrackTags(trackId: number, tags: Partial<FileTags>): Promise<any> {
    const res = await fetch(`${BASE_URL}/tracks/${trackId}/tags`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tags),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao atualizar tags');
    }
    return res.json();
  },

  // Playlists (M3U to SwingMusic)
  async getPlaylists(): Promise<{ total: number; playlists: any[] }> {
    const res = await fetch(`${BASE_URL}/playlists`);
    if (!res.ok) throw new Error('Falha ao buscar playlists');
    return res.json();
  },

  async getPlaylistDetail(filepath: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/playlists/detail?path=${encodeURIComponent(filepath)}`);
    if (!res.ok) throw new Error('Falha ao carregar detalhes da playlist');
    return res.json();
  },

  async createPlaylist(filepath: string, name?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/playlists/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath, name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao criar playlist no SwingMusic');
    }
    return res.json();
  },

  async deleteSwingPlaylist(playlistId: number): Promise<any> {
    const res = await fetch(`${BASE_URL}/playlists/${playlistId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Erro ao remover playlist do SwingMusic');
    return res.json();
  },

  async uploadPlaylistCover(playlistId: number, options: File | { file?: File; imageUrl?: string }): Promise<any> {
    let res: Response;
    if (options instanceof File) {
      const form = new FormData();
      form.append('image', options);
      res = await fetch(`${BASE_URL}/playlists/${playlistId}/cover`, {
        method: 'POST',
        body: form,
      });
    } else if (options.file) {
      const form = new FormData();
      form.append('image', options.file);
      res = await fetch(`${BASE_URL}/playlists/${playlistId}/cover`, {
        method: 'POST',
        body: form,
      });
    } else {
      res = await fetch(`${BASE_URL}/playlists/${playlistId}/cover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_url: options.imageUrl }),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao enviar capa da playlist');
    }
    return res.json();
  },

  // SwingMusic Customization (Users, Avatars, Fallback Assets, Client)
  async getSwingUsers(): Promise<{ total: number; users: any[] }> {
    const res = await fetch(`${BASE_URL}/swingmusic/users`);
    if (!res.ok) throw new Error('Falha ao buscar usuários do SwingMusic');
    return res.json();
  },

  async uploadUserAvatar(userId: number, imageBase64?: string, imageUrl?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/swingmusic/users/${userId}/avatar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: imageBase64, image_url: imageUrl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao enviar foto de perfil');
    }
    return res.json();
  },

  async deleteUserAvatar(userId: number): Promise<any> {
    const res = await fetch(`${BASE_URL}/swingmusic/users/${userId}/avatar`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Erro ao remover foto de perfil');
    return res.json();
  },

  async updateSwingUser(userId: number, data: any): Promise<any> {
    const res = await fetch(`${BASE_URL}/swingmusic/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Erro ao atualizar usuário');
    return res.json();
  },

  async getFallbackAssets(): Promise<{ total: number; assets: any[] }> {
    const res = await fetch(`${BASE_URL}/swingmusic/assets`);
    if (!res.ok) throw new Error('Falha ao buscar assets');
    return res.json();
  },

  async uploadFallbackAsset(name: string, fileBase64: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/swingmusic/assets/${name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_base64: fileBase64 }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao enviar asset');
    }
    return res.json();
  },

  async getClientInfo(): Promise<any> {
    const res = await fetch(`${BASE_URL}/swingmusic/client`);
    if (!res.ok) throw new Error('Falha ao buscar info do client');
    return res.json();
  },

  // System
  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch(`${BASE_URL}/system/status`);
    if (!res.ok) throw new Error('Erro ao buscar status do sistema');
    return res.json();
  },

  async saveSpotifyConfig(clientId: string, clientSecret: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/system/spotify-config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Erro ao validar credenciais do Spotify');
    }
    return res.json();
  },
};
