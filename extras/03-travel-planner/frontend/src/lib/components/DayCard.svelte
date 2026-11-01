<script lang="ts">
	import { Calendar, Clock, DollarSign } from 'lucide-svelte';
	import type { DayPlan } from '$lib/api';

	let { day }: { day: DayPlan } = $props();

	let dailyTotal = $derived(
		day.activities.reduce((sum, a) => sum + (a.cost || 0), 0),
	);
</script>

<div class="rounded-lg border bg-card p-5 shadow-sm">
	<div class="mb-4 flex items-center justify-between">
		<div class="flex items-center gap-2">
			<div
				class="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground"
			>
				{day.day}
			</div>
			<div>
				<h3 class="font-semibold text-foreground">Day {day.day}</h3>
				{#if day.date}
					<p class="flex items-center gap-1 text-xs text-muted-foreground">
						<Calendar class="h-3 w-3" />
						{day.date}
					</p>
				{/if}
			</div>
		</div>
		{#if day.theme}
			<span class="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
				{day.theme}
			</span>
		{/if}
	</div>

	<div class="space-y-3">
		{#each day.activities as activity}
			<div class="rounded-md border border-border/60 bg-background p-3">
				<div class="mb-1 flex items-start justify-between">
					<div class="flex items-center gap-2">
						<span class="flex items-center gap-1 text-xs font-medium text-primary">
							<Clock class="h-3 w-3" />
							{activity.time}
						</span>
						<span class="font-medium text-foreground">{activity.name}</span>
					</div>
					{#if activity.cost > 0}
						<span class="flex items-center gap-0.5 text-sm font-medium text-accent">
							<DollarSign class="h-3.5 w-3.5" />
							{activity.cost.toFixed(0)}
						</span>
					{:else}
						<span class="text-xs text-muted-foreground">Free</span>
					{/if}
				</div>
				<p class="text-sm text-muted-foreground">{activity.description}</p>
			</div>
		{/each}
	</div>

	<div class="mt-4 flex items-center justify-end border-t pt-3">
		<span class="flex items-center gap-1 text-sm font-semibold text-foreground">
			<DollarSign class="h-4 w-4 text-primary" />
			Day total: ${dailyTotal.toFixed(0)}
		</span>
	</div>
</div>
