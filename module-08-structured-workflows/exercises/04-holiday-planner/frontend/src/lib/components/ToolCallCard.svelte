<script lang="ts">
	import { Wrench, FileText } from 'lucide-svelte';

	let { type, name, content }: { type: 'call' | 'result'; name: string; content: string } = $props();
	let expanded = $state(false);

	const truncated = $derived(content.length > 200 ? content.slice(0, 200) + '...' : content);
</script>

<div class="mx-10 border rounded-lg overflow-hidden text-sm">
	<button
		onclick={() => (expanded = !expanded)}
		class="w-full flex items-center gap-2 px-3 py-2 bg-muted/50 hover:bg-muted transition-colors text-left"
	>
		{#if type === 'call'}
			<Wrench class="h-3.5 w-3.5 text-blue-500 shrink-0" />
			<span class="font-medium text-blue-600">Tool call:</span>
		{:else}
			<FileText class="h-3.5 w-3.5 text-green-500 shrink-0" />
			<span class="font-medium text-green-600">Result:</span>
		{/if}
		<span class="text-muted-foreground truncate">{name}</span>
		<span class="ml-auto text-muted-foreground text-xs">{expanded ? '▼' : '▶'}</span>
	</button>
	{#if expanded}
		<pre class="px-3 py-2 text-xs overflow-x-auto bg-background">{content}</pre>
	{:else if content}
		<pre class="px-3 py-2 text-xs overflow-x-auto bg-background text-muted-foreground">{truncated}</pre>
	{/if}
</div>
