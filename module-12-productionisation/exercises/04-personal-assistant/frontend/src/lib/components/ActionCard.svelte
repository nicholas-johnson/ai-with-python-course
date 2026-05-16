<script lang="ts">
	import { Calendar, Bell, FileText } from 'lucide-svelte';

	let { actionType, description }: { actionType: string; description: string } = $props();

	const iconMap: Record<string, typeof Calendar> = {
		calendar: Calendar,
		reminder: Bell,
		notes: FileText,
	};

	const labelMap: Record<string, string> = {
		calendar: 'Calendar updated',
		reminder: 'Reminder set',
		notes: 'Found in notes',
	};

	let resolvedType = $derived(
		actionType.includes('calendar') ? 'calendar' :
		actionType.includes('reminder') ? 'reminder' : 'notes'
	);

	let Icon = $derived(iconMap[resolvedType] ?? FileText);
	let label = $derived(labelMap[resolvedType] ?? 'Action completed');
</script>

<div class="flex items-start gap-3 px-4 py-3 my-2 rounded-lg bg-accent/10 border border-accent/20">
	<div class="flex-shrink-0 w-7 h-7 rounded-md bg-accent/20 flex items-center justify-center">
		<svelte:component this={Icon} class="w-4 h-4 text-accent" />
	</div>
	<div class="flex-1 min-w-0">
		<p class="text-xs font-medium text-accent">{label}</p>
		<p class="text-sm text-foreground mt-0.5">{description}</p>
	</div>
</div>
