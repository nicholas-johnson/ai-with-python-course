<script lang="ts">
	import { Calendar } from 'lucide-svelte';
	import type { CalendarEvent } from '$lib/api';

	let { event }: { event: CalendarEvent } = $props();
</script>

<div class="flex items-start gap-2.5 px-3 py-2 rounded-md hover:bg-muted/60 transition-colors">
	<Calendar class="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
	<div class="flex-1 min-w-0">
		<p class="text-sm font-medium text-foreground truncate">{event.title}</p>
		<p class="text-xs text-muted-foreground">
			{event.date}{#if event.time} &middot; {event.time}{/if}
			{#if event.location} &middot; {event.location}{/if}
		</p>
	</div>
</div>
