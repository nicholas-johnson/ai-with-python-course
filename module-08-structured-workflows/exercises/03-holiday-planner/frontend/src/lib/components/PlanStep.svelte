<script lang="ts">
	import { Check, X, Loader2, Clock } from 'lucide-svelte';
	import type { PlanStep } from '$lib/api';

	let { step }: { step: PlanStep } = $props();
</script>

<div class="flex items-start gap-3 py-2">
	<!-- Step number circle -->
	<div
		class="flex items-center justify-center h-7 w-7 rounded-full text-xs font-bold shrink-0 {step.status === 'done'
			? 'bg-green-100 text-green-700'
			: step.status === 'running'
				? 'bg-blue-100 text-blue-700'
				: step.status === 'failed'
					? 'bg-red-100 text-red-700'
					: 'bg-muted text-muted-foreground'}"
	>
		{#if step.status === 'done'}
			<Check class="h-3.5 w-3.5" />
		{:else if step.status === 'running'}
			<Loader2 class="h-3.5 w-3.5 animate-spin" />
		{:else if step.status === 'failed'}
			<X class="h-3.5 w-3.5" />
		{:else}
			{step.number}
		{/if}
	</div>

	<div class="flex-1 min-w-0">
		<p
			class="text-sm leading-snug {step.status === 'done'
				? 'text-foreground'
				: step.status === 'running'
					? 'text-blue-700 font-medium'
					: step.status === 'failed'
						? 'text-red-600'
						: 'text-muted-foreground'}"
		>
			{step.description}
		</p>
		{#if step.result}
			<p class="text-xs text-muted-foreground mt-1 leading-relaxed">{step.result}</p>
		{/if}
	</div>
</div>
