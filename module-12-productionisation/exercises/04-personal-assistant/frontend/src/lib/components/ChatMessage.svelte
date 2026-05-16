<script lang="ts">
	let { role, content, streaming = false }: { role: 'user' | 'assistant'; content: string; streaming?: boolean } = $props();
</script>

<div class="flex gap-3 {role === 'user' ? 'flex-row-reverse' : ''}">
	{#if role === 'assistant'}
		<div class="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
			<span class="text-primary-foreground text-sm font-semibold">C</span>
		</div>
	{/if}

	<div
		class="max-w-[75%] px-4 py-2.5 rounded-2xl {role === 'user'
			? 'bg-primary text-primary-foreground rounded-br-md'
			: 'bg-muted text-foreground rounded-bl-md'}"
	>
		<p class="text-sm leading-relaxed whitespace-pre-wrap">{content}{#if streaming}<span class="inline-block w-1.5 h-4 bg-current opacity-60 animate-pulse ml-0.5"></span>{/if}</p>
	</div>

	{#if role === 'user'}
		<div class="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
			<span class="text-muted-foreground text-sm font-semibold">U</span>
		</div>
	{/if}
</div>
