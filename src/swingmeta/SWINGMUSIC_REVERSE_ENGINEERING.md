# 🧠 Engenharia Reversa e Arquitetura Interna do SwingMusic & SwingMeta

Este documento consolida todo o conhecimento adquirido através de engenharia reversa e análise de código-fonte do ecossistema **SwingMusic** e sua extensão **SwingMeta**. Serve como referência técnica definitiva sobre o funcionamento do banco de dados, ciclo de vida de entidades em memória (RAM), geração de hashes, processamento de tags e gerenciamento de imagens/avatares.

---

## 1. 🏗️ Arquitetura de Armazenamento e Volumes

O SwingMusic organiza sua estrutura de dados e arquivos estáticos a partir de um diretório base (`SWINGMUSIC_CONFIG_DIR`, por padrão `~/.config/swingmusic` no host ou `/config/swingmusic` no Docker):

```text
/config/swingmusic/
├── swingmusic.db             # Banco de dados SQLite unificado
├── settings.json             # Configurações do servidor e pastas monitoradas
├── client/                   # WebClient (assets frontend extraídos do SwingMusic)
└── images/                   # Repositório de mídias e capas
    ├── artists/
    │   ├── large/            # 500x500 (página de detalhes do artista)
    │   ├── medium/           # 250x250 (grids de artistas)
    │   └── small/            # 128x128 (listas compactas)
    ├── playlists/            # Capas de playlists (512x512 e thumb_ 250x250)
    ├── thumbnails/           # Miniaturas de álbuns (large, medium, small, xsmall)
    ├── users/                # Avatares de usuários (user_{id}.webp 256x256)
    └── mixes/                # Imagens de mixes gerados
```

---

## 2. 🗄️ Banco de Dados SQLite (`swingmusic.db`)

Historicamente, o SwingMusic utilizava dois bancos (`swingmusic.db` e `userdata.db`). Nas versões recentes, todas as tabelas foram unificadas no arquivo principal `swingmusic.db`.

### 2.1. Tabela `playlist`
Estrutura exata esperada pelo backend e frontend do SwingMusic:

| Coluna | Tipo | Descrição e Regras |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Identificador sequencial da playlist. |
| `name` | `VARCHAR` | Nome da playlist exibido na UI. |
| `last_updated`| `DATETIME / VARCHAR` | Formato obrigatório: `YYYY-MM-DD HH:MM:SS` (ex: `2026-08-21 04:21:42`). |
| `image` | `VARCHAR` | Nome do arquivo principal (ex: `pl_1_1787286101.webp`). Nulo se não houver capa customizada. |
| `userid` | `INTEGER` | ID do proprietário da playlist (padrão `1` para o administrador). |
| `settings` | `JSON` | Objeto de flags da UI: `{"has_gif": false, "banner_pos": 50, "square_img": true, "pinned": false}`. |
| `trackhashes` | `JSON` | Array JSON de strings com os hashes das músicas: `["hash1", "hash2", ...]`. |
| `extra` | `JSON` | Metadados extras opcionais (`null` ou `{}`). |

### 2.2. Tabela `user`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Identificador do usuário. |
| `username` | `VARCHAR` | Nome de login único. |
| `password` | `VARCHAR` | Hash SHA256 da senha. |
| `image` | `VARCHAR` | Nome do arquivo de avatar em `images/users/` (ex: `user_1.webp`). |
| `roles` | `JSON` | Array JSON de papéis (ex: `["admin"]` ou `["user"]`). |
| `extra` | `JSON` | Objeto JSON com `firstname`, `lastname`, `email`, etc. |

> ℹ️ **Comportamento do Frontend do SwingMusic para Usuários:**  
> O frontend oficial do SwingMusic (`AvatarWithDropdown`) renderiza o avatar do usuário através da biblioteca **BoringAvatars** (gerador de SVG vetorial a partir das iniciais do username). O backend armazena o campo `image`, mas a interface web padrão ainda não consome tags `<img>` para avatares de usuários.

### 2.3. Tabela `track`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Identificador da faixa. |
| `title` | `VARCHAR` | Título da música lido da tag ID3/FLAC. |
| `album` | `VARCHAR` | Nome do álbum. |
| `artists` | `VARCHAR` | String de artistas (pode conter separadores `;` ou `/`). |
| `albumartists`| `VARCHAR` | Artistas do álbum. |
| `trackhash` | `VARCHAR` | Hash gerado durante o scan da biblioteca. |
| `albumhash` | `VARCHAR` | Hash do álbum para associar com capas em `thumbnails/`. |
| `filepath` | `VARCHAR` | Caminho absoluto do arquivo de áudio no sistema de arquivos. |
| `duration` | `INTEGER` | Duração em segundos. |
| `disc` / `track` | `INTEGER` | Número do disco e da faixa. |
| `extra` | `JSON` | Metadados técnicos (bitrate, samplerate, hashinfo, letras). |

---

## 3. 🔑 Engenharia Reversa do Sistema de Hashes (`TrackStore`)

Esta foi a descoberta mais crítica do projeto: **o hash armazenado na coluna `track.trackhash` do SQLite pode ser diferente do hash ativo mantido pelo SwingMusic na memória RAM.**

### 3.1. Por que ocorre essa divergência?
1. **Scans Legados:** Versões antigas do scanner gravavam o hash usando SHA1 truncado (`hashlib.sha1(...)[:5] + [-5:]`).
2. **Ciclo de Vida em Memória (`Track.__post_init__`):** Ao iniciar, o SwingMusic lê o banco de dados e reconstrói todos os objetos `Track`. Durante esse processo, ele executa o método `Track.recreate_trackhash()`, que **recalcula o hash de cada música usando o algoritmo XXH3_64 e normalizações de texto**.
3. **Lookup de Playlists:** Quando o usuário abre uma playlist, o SwingMusic busca os hashes em `TrackStore.trackhashmap` (na memória RAM). Se a playlist tiver o hash do banco antigo ou um hash com divergência de normalização, o SwingMusic não encontra o objeto e retorna `[]` (faixa vazia).

---

### 3.2. Regras Exatas de Normalização do Hash em Memória

Para que o SwingMeta crie playlists 100% compatíveis com o SwingMusic sem exigir rescans, o SwingMeta implementa o método `compute_runtime_trackhash()`:

#### A. Algoritmo Base de Hashing (`create_hash`):
```python
def create_hash(*args: str, decode: bool = False) -> str:
    def remove_non_alnum(token: str) -> str:
        token = token.lower().strip().replace(" ", "")
        t = "".join(c for c in token if c.isalnum())
        return t if t != "" else token

    str_ = "".join(remove_non_alnum(t) for t in args)
    if decode:
        str_ = unidecode(str_)
    return xxhash.xxh3_64(str_.encode("utf-8")).hexdigest()
```
* **Atenção à flag `decode=False`:** O SwingMusic padrão usa `decode=False`, preservando caracteres UTF-8 na string antes de passar pelo XXH3.

#### B. Normalização de Múltiplos Artistas:
- Strings de artistas como `Eve/Drag-On` ou `NX Zero; Tulio Dek` são divididas por regex `[;/]+`.
- Cada artista individual é tratado como um token separado na ordem em que aparece.

#### C. Extração de Artistas Participantes (*Featured Artists*):
- O SwingMusic detecta `(feat. ...)`, `(ft. ...)`, `(featuring ...)`, `[with ...]` no título da música.
- Os artistas participantes são removidos do título e anexados à lista de artistas para a composição do hash.

#### D. Limpeza de Tags de Produtor e Remasterização:
- Remoção de tags como `(prod. by ...)` ou `prod. DJ XYZ`.
- Remoção de sufixos de remasterização como `(Remastered 2011)` ou `- Remaster`.

#### E. Limpeza de Versões e Edições de Álbum:
- Versões de álbum entre parênteses/colchetes são removidas pelo SwingMusic (ex: `My Worlds (International Version)` torna-se `My Worlds`, `Hybrid Theory (Bonus Track Version)` torna-se `Hybrid Theory`).
- Palavras-chave filtradas: `deluxe`, `edition`, `international`, `bonus track`, `expanded`, `remaster`, `anniversary`, `special`, `complete`, `instrumental`, `acoustic`, `unplugged`, `mono`, `stereo`, etc.

#### F. Fórmula Final do Hash de Faixa:
```
trackhash = create_hash(Título Limpo, Álbum Limpo, Artista_1, Artista_2, ..., decode=False)
```

> 🧪 **Validação:** Essa fórmula foi testada contra 100% das 485 faixas do catálogo real, obtendo **485/485 (100.00%) de precisão** com a memória RAM do servidor SwingMusic.

---

## 4. 🖼️ Padrões de Imagens e Miniaturas

### 4.1. Playlists
O SwingMusic exige **dois arquivos** para capas de playlists no diretório `images/playlists/`:
1. **Capa Principal:** `{filename}.webp` (512x512 pixels, WebP a 90% de qualidade) — exibida na visão detalhada / cabeçalho da playlist.
2. **Miniatura:** `thumb_{filename}.webp` (250x250 pixels, WebP) — exigida pelo SwingMusic para cards, listagens laterais e miniaturas da biblioteca.

### 4.2. Artistas
- **Diretórios:** `images/artists/large/` (500x500), `images/artists/medium/` (250x250), `images/artists/small/` (128x128).
- **Detecção de Silhuetas Genéricas (Filtro 'Sem Foto'):** Quando o SwingMusic faz busca online no Deezer e não encontra foto, ele baixa uma cópia de um avatar genérico de silhueta. O SwingMeta identifica essas imagens falsas através dos seguintes hashes MD5:
  - `49a5d317ed0eedc6c1d7cdbc42d2fd22` (1.414 bytes)
  - `44ea537d85bf5c966c584b044d562e72` (1.414 bytes)

### 4.3. Prevenção de Cache Estático (Cache-Busting)
Todas as rotas de imagens servidas pela API do SwingMeta implementam:
- `Cache-Control: no-cache, must-revalidate`
- Parâmetro dinâmico de timestamp `?t={mtime}` ou `?t={Date.now()}` nas URLs de retorno, garantindo atualização visual instantânea na interface web.

---

## 5. 🛠️ Correções Aplicadas no Código do SwingMusic

Durante a análise, dois pontos nativos do backend do SwingMusic foram corrigidos no repositório:

1. **Bug do Slice de Faixas em Playlists (`src/swingmusic/api/playlist.py:243`):**
   - *Problema:* O SwingMusic original usava `query.limit = len(playlist.trackhashes) - 1`. Em playlists de 1 música, `limit` tornava-se `0`, resultando em `trackhashes[0:0] == []` (lista vazia).
   - *Correção:* Alterado para `query.limit = len(playlist.trackhashes)`.
2. **Otimização de Build Multi-Arch Docker (`src/swingmeta/Dockerfile`):**
   - *Problema:* A compilação do frontend Vue/Vite dentro da emulação QEMU para `linux/arm64` demorava mais de 40 minutos.
   - *Correção:* Adicionado `--platform=$BUILDPLATFORM` no estágio `node:20-alpine`, fazendo com que a compilação ocorra nativamente na CPU do host em segundos, reduzindo o tempo de build para cerca de 1 minuto.

---

## 6. 🔗 Interoperabilidade: Pasta Compartilhada de Artes de Artistas

Para permitir que outros servidores de mídia (ex: Navidrome) reaproveitem as fotos de artistas mantidas pelo SwingMeta sem acoplamento direto entre os dois projetos, existe uma pasta plana opcional, de propriedade do SwingMeta, configurável via `SM_ARTISTARTPRIORITY` (`services/shared_artist_art.py`).

- **Formato:** `{NomeDoArtista}.jpg` (nome exato do artista, com caracteres inválidos de sistema de arquivos — `\ / : * ? " < > |` — substituídos por `_`), sempre convertido para JPEG qualidade 95, **sem redimensionar** (mantém a maior resolução disponível na origem).
- **Quando é atualizada:** a cada upload/aplicação de foto via `POST /api/artists/<hash>/image`, antes do SwingMusic fazer seu próprio crop+resize destrutivo para WebP 500/256/128px. Também é removida ao deletar a foto do artista.
- **Exportação em lote:** `POST /api/artists/export-shared-art` converte as fotos já existentes (o `.webp` 500x500 de `artist_images_lg`, teto de qualidade disponível para fotos anteriores a essa feature) para `.jpg` na pasta compartilhada.
- **Consumo pelo Navidrome (referência, não é responsabilidade do SwingMeta):** monte o mesmo diretório como somente leitura e configure `ND_ARTISTIMAGEFOLDER=<mesmo caminho>` + inclua `image-folder` em `ND_ARTISTARTPRIORITY`. O Navidrome casa arquivos pelo nome-base (case-insensitive) igual ao nome do artista ou ao MusicBrainz ID — como o SwingMusic não versiona MBID, o casamento é sempre por nome.
- **Se for necessário reaproveitar esse padrão para outro tipo de mídia (álbuns, etc.), mantenha o serviço agnóstico** — não referencie "Navidrome" fora de comentários/documentação, já que a pasta pode ser consumida por qualquer servidor compatível com essa convenção.

## 7. 📌 Guia de Manutenção e Extensões Futuras

- Ao criar novas funcionalidades que manipulem playlists, **sempre utilize `compute_runtime_trackhash()`** em vez de ler cegamente a coluna `trackhash` do SQLite.
- Ao salvar capas de playlists, gere sempre a versão principal e a versão com prefixo `thumb_`.
- Caso sejam criados novos separadores de artistas na configuração do usuário (`settings.json -> artistSeparators`), estes devem ser refletidos no regex de divisão de artistas.
