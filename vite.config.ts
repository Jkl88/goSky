import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify from 'vite-plugin-vuetify';
import { fileURLToPath, URL } from 'node:url';

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';
const slugPattern = /^\/[A-Za-z0-9$@!%#]{1,6}$/;

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5175,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
      '/health': { target: apiTarget, changeOrigin: true },
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const path = (req.url || '').split('?')[0];
        if (slugPattern.test(path)) {
          const target = new URL(path, apiTarget);
          fetch(target.toString(), {
            method: req.method || 'GET',
            headers: { cookie: req.headers.cookie || '' },
            redirect: 'manual',
          })
            .then(async (r) => {
              res.statusCode = r.status;
              r.headers.forEach((v, k) => {
                if (k.toLowerCase() !== 'transfer-encoding') res.setHeader(k, v);
              });
              const body = await r.arrayBuffer();
              res.end(Buffer.from(body));
            })
            .catch(() => {
              res.statusCode = 502;
              res.end('Bad Gateway');
            });
          return;
        }
        next();
      });
    },
  },
});
