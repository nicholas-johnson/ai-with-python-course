<script lang="ts">
	import { User, Bot } from 'lucide-svelte';
	import { marked } from 'marked';
	import type { Message } from '$lib/api';

	let { message }: { message: Message } = $props();

	marked.setOptions({ breaks: true, gfm: true });

	let html = $derived(
		message.role === 'assistant' ? marked.parse(message.content) : ''
	);
</script>

{#if message.role === 'user'}
	<div class="flex gap-3 justify-end">
		<div class="bg-primary text-primary-foreground rounded-lg px-4 py-3 max-w-[80%]">
			<p class="text-sm whitespace-pre-wrap">{message.content}</p>
		</div>
		<div class="flex items-start justify-center h-8 w-8 rounded-full bg-primary text-primary-foreground shrink-0">
			<User class="h-4 w-4 mt-2" />
		</div>
	</div>
{:else if message.role === 'assistant'}
	<div class="flex gap-3">
		<div class="flex items-start justify-center h-8 w-8 rounded-full bg-muted shrink-0">
			<Bot class="h-4 w-4 mt-2" />
		</div>
		<div class="prose prose-sm dark:prose-invert bg-muted rounded-lg px-4 py-3 max-w-[80%]">
			{@html html}
		</div>
	</div>
{/if}
