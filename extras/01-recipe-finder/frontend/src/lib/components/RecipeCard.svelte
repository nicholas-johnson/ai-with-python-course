<script lang="ts">
	import { Clock, Users, ChefHat, AlertTriangle, Zap } from 'lucide-svelte';
	import type { Recipe } from '$lib/api';

	let { recipe, cached = false }: { recipe: Recipe; cached?: boolean } = $props();

	const displayIngredients = $derived(recipe.ingredients.slice(0, 5));
	const remainingCount = $derived(Math.max(0, recipe.ingredients.length - 5));

	const difficultyColor = $derived(
		recipe.difficulty === 'Easy'
			? 'bg-green-100 text-green-700'
			: recipe.difficulty === 'Medium'
				? 'bg-amber-100 text-amber-700'
				: 'bg-red-100 text-red-700',
	);
</script>

<div
	class="group relative bg-card rounded-lg border shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
>
	{#if cached || recipe.cached}
		<div class="absolute top-3 right-3 z-10">
			<span
				class="inline-flex items-center gap-1 rounded-full bg-accent/20 px-2 py-0.5 text-xs font-medium text-accent"
			>
				<Zap class="h-3 w-3" />
				Cached
			</span>
		</div>
	{/if}

	<div class="p-5">
		<div class="flex items-start gap-3 mb-3">
			<div
				class="flex items-center justify-center h-10 w-10 rounded-lg bg-primary/10 text-primary shrink-0"
			>
				<ChefHat class="h-5 w-5" />
			</div>
			<div class="min-w-0 flex-1">
				<h3
					class="font-semibold text-foreground leading-tight group-hover:text-primary transition-colors"
				>
					{recipe.title}
				</h3>
				<div class="flex items-center gap-2 mt-1">
					<span class="inline-block rounded-full bg-primary/10 text-primary px-2 py-0.5 text-xs font-medium">
						{recipe.cuisine}
					</span>
					<span class="inline-block rounded-full {difficultyColor} px-2 py-0.5 text-xs font-medium">
						{recipe.difficulty}
					</span>
				</div>
			</div>
		</div>

		{#if recipe.description}
			<p class="text-sm text-muted-foreground mb-3 line-clamp-2">{recipe.description}</p>
		{/if}

		<div class="flex items-center gap-4 text-sm text-muted-foreground mb-3">
			<span class="inline-flex items-center gap-1">
				<Clock class="h-3.5 w-3.5" />
				{recipe.cook_time_minutes} min
			</span>
			<span class="inline-flex items-center gap-1">
				<Users class="h-3.5 w-3.5" />
				{recipe.servings} servings
			</span>
		</div>

		<div class="flex flex-wrap gap-1.5 mb-3">
			{#each displayIngredients as ingredient}
				<span class="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
					{ingredient}
				</span>
			{/each}
			{#if remainingCount > 0}
				<span class="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
					+{remainingCount} more
				</span>
			{/if}
		</div>

		{#if recipe.allergens && recipe.allergens.length > 0}
			<div class="flex items-center gap-1.5 pt-2 border-t">
				<AlertTriangle class="h-3.5 w-3.5 text-amber-500 shrink-0" />
				<span class="text-xs text-amber-600 font-medium">
					{recipe.allergens.join(', ')}
				</span>
			</div>
		{/if}
	</div>
</div>
