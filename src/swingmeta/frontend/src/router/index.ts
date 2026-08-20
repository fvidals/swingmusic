import { createRouter, createWebHistory } from 'vue-router';
import ArtistsView from '../views/ArtistsView.vue';
import ArtistDetailView from '../views/ArtistDetailView.vue';
import TracksView from '../views/TracksView.vue';
import PlaylistsView from '../views/PlaylistsView.vue';
import SwingMusicView from '../views/SwingMusicView.vue';
import SettingsView from '../views/SettingsView.vue';

const routes = [
  {
    path: '/',
    name: 'artists',
    component: ArtistsView,
  },
  {
    path: '/artists/:artisthash',
    name: 'artist-detail',
    component: ArtistDetailView,
  },
  {
    path: '/tracks',
    name: 'tracks',
    component: TracksView,
  },
  {
    path: '/playlists',
    name: 'playlists',
    component: PlaylistsView,
  },
  {
    path: '/swingmusic',
    name: 'swingmusic',
    component: SwingMusicView,
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});
