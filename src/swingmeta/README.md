# 🎵 SwingMeta - Side-load Metadata & Image Editor

**SwingMeta** é uma aplicação companheira (*sidecar / side-load*) desenvolvida para rodar lado a lado com o [Swing Music](https://github.com/swingmx/swingmusic), compartilhando o mesmo ponto de montagem de volumes (`/config` e `/music`).

O SwingMeta resolve as limitações de edição de metadados do Swing Music, fornecendo uma interface visual moderna em **Vue 3 + Vite** e um backend em **Python (Flask + Mutagen + Pillow)**.

---

## ✨ Funcionalidades Principais

- 🎨 **Gerenciamento Completo de Fotos de Artistas:**
  - Upload via *Drag & Drop* com recorte proporcional 1:1.
  - Conversão automática para **WebP** nas 3 resoluções exigidas pelo SwingMusic: `large` (500px), `medium` (256px) e `small` (128px).
  - Extração automática da paleta de cores dominante (`colorgram`) e `blurhash` para carregamento fluido.
- 🌐 **Busca Online Multi-Provedores:**
  - **Zero Configuração:** Busca instantânea no **Deezer** e **MusicBrainz** para encontrar fotos oficiais e biografias com 1 clique.
  - **Opcional (Spotify):** Integração com a API do Spotify (via Client ID & Secret) para consultar o catálogo do Spotify.
- 📝 **Editor de Biografias de Artistas:**
  - Permite escrever e salvar biografias diretamente na tabela `artistdata` do banco `userdata.db`.
- 👤 **Customização de Usuários & Avatares do SwingMusic:**
  - Lista todos os usuários cadastrados no `userdata.db` (admin, guest, etc.).
  - Upload e recorte de foto de perfil customizada (salvo em WebP 256x256 e sincronizado com a tabela `user`).
  - Edição de nome de exibição, primeiro nome e email.
- 🎨 **Substituição de Imagens Padrão & Assets de Fallback:**
  - Substitui as imagens padrão do SwingMusic (`artist.webp`, `default.webp`, `playlist.svg`, `album.svg`).
  - Permite trocar as artes padrão para artistas sem foto ou álbuns sem capa por suas próprias artes.
- 🌐 **Diagnóstico do WebClient:**
  - Inspeciona o diretório `/config/client` mostrando versão instalada, total de arquivos e localização.
- 🎶 **Importador de Playlists M3U → SwingMusic:**
  - Escaneia e detecta arquivos `.m3u` e `.m3u8` nos diretórios de música (como na pasta `Playlists/`).
  - Identifica automaticamente os IDs e `trackhash` de cada música correspondente na biblioteca do SwingMusic.
  - Cria e sincroniza a Playlist nativa no SwingMusic com 1 clique.
- 🏷️ **Editor de Tags de Áudio (ID3) com Mutagen:**
  - Edição direta de metadados nos arquivos de áudio físicos (`.mp3`, `.flac`, `.m4a`, `.ogg`, `.opus`).
  - Sincronização automática com a tabela `track` do `swingmusic.db`.
- 📊 **Diagnóstico de Volumes & Conexões:**
  - Painel de status em tempo real que valida os pontos de montagem (`swingmusic.db`, `userdata.db`, pasta de imagens e `/music`).
- 🔗 **Pasta Compartilhada de Artes de Artistas (multi-servidor):**
  - Mantém automaticamente, em caminho fixo (`/shared/artist-art`, sem configuração necessária), uma pasta plana com as fotos de artistas em qualidade máxima (`{NomeDoArtista}.jpg`), atualizada sempre que uma foto é definida no SwingMeta.
  - Pensada para ser montada como volume somente leitura em outros servidores de mídia (ex: Navidrome via `ND_ARTISTIMAGEFOLDER` + `ND_ARTISTARTPRIORITY=image-folder,...`), sem acoplamento — o SwingMeta é o dono da pasta, o consumidor é livre.
  - Botão de exportação em lote para migrar fotos já existentes no SwingMusic para a pasta compartilhada.

---

## 🚀 Como Executar com Docker Compose (Recomendado)

O SwingMeta foi desenhado para rodar no mesmo host do Swing Music compartilhando a mesma pasta de configuração.

Crie ou atualize o seu arquivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Servidor principal do Swing Music
  swingmusic:
    image: swingmx/swingmusic:latest
    container_name: swingmusic
    restart: unless-stopped
    ports:
      - "1970:1970"
    volumes:
      - ./config:/config
      - ./music:/music
    environment:
      - SWINGMUSIC_IN_DOCKER=1

  # SwingMeta (Editor de Metadados)
  swingmeta:
    build:
      context: ./src/swingmeta
      dockerfile: Dockerfile
    container_name: swingmeta
    restart: unless-stopped
    ports:
      - "1971:1971"
    volumes:
      - ./config:/config    # Mesmo volume do Swing Music
      - ./music:/music      # Mesmo volume do Swing Music
      # Pasta compartilhada de artes de artistas (caminho fixo /shared/artist-art,
      # sem necessidade de variável de ambiente), leitura/escrita
      - ./shared/artist-art:/shared/artist-art
    environment:
      - SWING_CONFIG_DIR=/config
      - SWING_MUSIC_DIR=/music
      - SWINGMETA_PORT=1971
      # Opcional: Spotify Developer API
      - SPOTIFY_CLIENT_ID=
      - SPOTIFY_CLIENT_SECRET=
    depends_on:
      - swingmusic

  # Opcional: Navidrome consumindo a mesma pasta de artes de artistas
  navidrome:
    image: deluan/navidrome:latest
    container_name: navidrome
    restart: unless-stopped
    ports:
      - "4533:4533"
    volumes:
      - ./navidrome-data:/data
      - ./music:/music:ro
      - ./shared/artist-art:/shared/artist-art:ro   # Mesma pasta do SwingMeta, somente leitura
    environment:
      - ND_MUSICFOLDER=/music
      - ND_ARTISTIMAGEFOLDER=/shared/artist-art
      # "image-folder" primeiro: a arte mantida pelo SwingMeta é a fonte primária
      - ND_ARTISTARTPRIORITY=image-folder,artist.*,album/artist.*,external
```

Suba os contêineres:
```bash
docker compose up -d --build
```

Acesse:
- **Swing Music:** `http://seu-servidor:1970`
- **SwingMeta:** `http://seu-servidor:1971`

---

## 💻 Como Executar Localmente (Desenvolvimento)

### 1. Backend (Python):
```bash
cd src/swingmeta/backend
pip install -r requirements.txt
python app.py
```

### 2. Frontend (Vue 3 + Vite):
```bash
cd src/swingmeta/frontend
npm install
npm run dev
```

Acesse o frontend em `http://localhost:3000` (com proxy automático para o backend na porta `1971`).

---

## 📁 Estrutura de Pastas do Projeto

```text
src/swingmeta/
├── backend/
│   ├── app.py                 # Servidor Flask e rotas SPA
│   ├── config.py              # Resolução de volumes (/config, /music)
│   ├── database.py            # Conexão SQLite (swingmusic.db e userdata.db)
│   ├── services/
│   │   ├── artist_service.py  # Agregação e metadados de artistas
│   │   ├── image_service.py   # Redimensionamento WebP, paleta de cores e blurhash
│   │   ├── online_search.py   # Deezer, MusicBrainz, Spotify e iTunes API
│   │   └── tag_service.py     # Leitura/escrita de tags ID3 via Mutagen
│   └── routes/                # Endpoints REST (/api/artists, /api/tracks, etc.)
├── frontend/
│   ├── src/
│   │   ├── components/        # Componentes Vue (Uploader, Modais, Cards, Navbar)
│   │   ├── views/             # Telas: Artistas, Detalhes, Tags, Configurações
│   │   └── api/client.ts      # Cliente de API TypeScript
├── Dockerfile                 # Multi-stage build (Node + Python)
├── docker-compose.yml         # Exemplo de deploy
└── run.py                     # Inicializador local
```
