import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	optimizeDeps: {
		exclude: ['lucide-svelte'],
	},
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				rewrite: (path) => path.replace(/^\/api/, ''),
			},
		},
	},
});
