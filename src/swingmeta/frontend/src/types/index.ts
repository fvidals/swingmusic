export interface Artist {
  artisthash: string;
  name: string;
  album_count: number;
  track_count: number;
  duration: number;
  has_image: boolean;
  has_bio: boolean;
  bio?: string;
  colors?: string[];
  blurhash?: string;
  info?: Record<string, any>;
  extra?: Record<string, any>;
  image?: string | null;
  image_lg?: string | null;
}

export interface ArtistDetail extends Artist {
  tracks: Track[];
  albums: AlbumSummary[];
}

export interface AlbumSummary {
  albumhash: string;
  title: string;
  date?: number;
  cover?: string;
}

export interface Track {
  id: number;
  title: string;
  artists: any;
  albumartists?: any;
  album: string;
  albumhash: string;
  duration: number;
  track?: number;
  disc?: number;
  date?: number;
  genres?: string;
  bitrate?: number;
  filepath: string;
  last_mod?: number;
  has_cover?: boolean;
  cover_url?: string | null;
  cover_url_lg?: string | null;
}

export interface OnlineAlbumCoverCandidate {
  provider: string;
  album: string;
  artist?: string;
  image_url: string;
  thumbnail_url: string;
  nb_tracks?: number;
  total_tracks?: number;
  track_count?: number;
  year?: string;
  genre?: string;
  link?: string;
}

export interface OnlinePlaylistCoverCandidate {
  provider: 'Spotify' | 'Deezer' | 'Apple Music' | string;
  title: string;
  creator?: string;
  image_url: string;
  thumbnail_url: string;
  track_count?: number;
  description?: string;
  link?: string;
}

export interface FileTags {
  filepath: string;
  filename: string;
  format: string;
  title: string;
  artist: string;
  album: string;
  albumartist: string;
  year: string;
  tracknumber: string;
  discnumber: string;
  genre: string;
}

export interface OnlineImageCandidate {
  provider: 'Deezer' | 'Spotify' | 'iTunes' | 'MusicBrainz';
  name?: string;
  image_url?: string;
  thumbnail_url?: string;
  nb_fan?: number;
  nb_album?: number;
  genres?: string[];
  popularity?: number;
  link?: string;
}

export interface M3UPlaylist {
  name: string;
  filename: string;
  filepath: string;
  relative_path: string;
  total_tracks: number;
  matched_tracks: number;
  match_rate: number;
  is_created_in_swing: boolean;
  has_local_cover: boolean;
  local_cover_url?: string | null;
  swing_playlist?: {
    id: number;
    name: string;
    last_updated: number;
    track_count: number;
    trackhashes: string[];
    image?: string | null;
    has_image?: boolean;
    image_url?: string | null;
  };
}

export interface M3UTrackItem {
  raw_path: string;
  resolved_path: string;
  filename: string;
  title: string;
  duration: number;
  matched: boolean;
  track_id?: number | null;
  trackhash?: string | null;
  db_title?: string;
  db_artists?: string;
  db_album?: string;
  db_filepath?: string;
  db_duration?: number;
  artist?: string;
  album?: string;
}

export interface M3UDetail {
  name: string;
  filename: string;
  filepath: string;
  total_tracks: number;
  matched_count: number;
  tracks: M3UTrackItem[];
  is_created: boolean;
  swing_playlist?: any;
}

export interface SwingUser {
  id: number;
  username: string;
  image?: string | null;
  avatar_url?: string | null;
  has_custom_avatar: boolean;
  roles: string[];
  is_admin: boolean;
  is_guest: boolean;
  firstname?: string;
  lastname?: string;
  email?: string;
  extra?: Record<string, any>;
}

export interface FallbackAsset {
  name: string;
  label: string;
  type: string;
  exists: boolean;
  size_bytes: number;
  url?: string | null;
  filepath: string;
}

export interface ClientInfo {
  exists: boolean;
  is_patched?: boolean;
  version: string;
  path: string;
  total_files: number;
}

export interface MountPointInfo {
  path: string;
  label: string;
  exists: boolean;
  writable: boolean;
  track_count: number;
  source: string;
  is_swing_root?: boolean;
}

export interface SwingMetaSettings {
  embed_audio_tags: boolean;
  spotify_client_id?: string;
  spotify_client_secret?: string;
}

export interface SystemStatus {
  status: string;
  version: string;
  paths: {
    config_dir: string;
    swingmusic_db: string;
    userdata_db: string;
    images_dir: string;
    music_dir: string;
  };
  mounts: {
    swingmusic_db_exists: boolean;
    userdata_db_exists: boolean;
    images_dir_exists: boolean;
    music_dir_exists: boolean;
  };
  mount_points?: MountPointInfo[];
  shared_artist_art?: {
    path: string;
    is_mounted: boolean;
    image_count: number;
  };
  stats: {
    track_count: number;
    artist_image_count: number;
  };
  settings?: SwingMetaSettings;
  spotify: {
    configured: boolean;
    client_id: string;
  };
}

export interface BackupSummary {
  exists: boolean;
  config_dir: string;
  total_size_bytes: number;
  total_size_mb: number;
  total_files: number;
  database_count: number;
  image_count: number;
  images_size_bytes: number;
  images_size_mb: number;
  databases: Array<{
    name: string;
    relative_path: string;
    size_bytes: number;
    size_mb: number;
  }>;
}

