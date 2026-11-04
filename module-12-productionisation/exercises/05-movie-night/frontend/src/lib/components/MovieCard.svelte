<script lang="ts">
  import { Star } from 'lucide-svelte';
  import type { Movie } from '$lib/api';

  let { movie }: { movie: Movie } = $props();
</script>

<div class="rounded-lg bg-card border border-border p-5 flex flex-col gap-3 hover:border-primary/50 transition-colors">
  <div class="flex items-start justify-between gap-3">
    <div>
      <h3 class="text-lg font-semibold text-foreground">{movie.title}</h3>
      <p class="text-sm text-muted-foreground">{movie.year} &middot; {movie.director}</p>
    </div>
    <div class="flex items-center gap-1 shrink-0 text-accent">
      <Star class="w-4 h-4 fill-current" />
      <span class="text-sm font-medium">{movie.rating.toFixed(1)}</span>
    </div>
  </div>

  {#if movie.genres.length}
    <div class="flex flex-wrap gap-1.5">
      {#each movie.genres as genre}
        <span class="px-2 py-0.5 rounded-md bg-primary/15 text-primary text-xs font-medium">
          {genre}
        </span>
      {/each}
    </div>
  {/if}

  {#if movie.explanation}
    <p class="text-sm text-muted-foreground italic leading-relaxed">
      &ldquo;{movie.explanation}&rdquo;
    </p>
  {/if}

  {#if movie.cast?.length}
    <p class="text-xs text-muted-foreground">
      <span class="text-foreground/70">Cast:</span> {movie.cast.slice(0, 4).join(', ')}
    </p>
  {/if}

  {#if movie.mood_tags?.length}
    <div class="flex flex-wrap gap-1.5 pt-1 border-t border-border">
      {#each movie.mood_tags as tag}
        <span class="px-2 py-0.5 rounded-md bg-accent/15 text-accent text-xs">
          {tag}
        </span>
      {/each}
    </div>
  {/if}
</div>
