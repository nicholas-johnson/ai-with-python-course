<script lang="ts">
  import { Film, Search, Database, BarChart3 } from 'lucide-svelte';
  import { recommendMovies, queryData } from '$lib/api';
  import type { Movie, DataQueryResponse } from '$lib/api';
  import MovieCard from '$lib/components/MovieCard.svelte';
  import DataTable from '$lib/components/DataTable.svelte';

  let activeTab: 'mood' | 'data' = $state('mood');

  // Mood search state
  let moodQuery = $state('');
  let moodLoading = $state(false);
  let moodResults: Movie[] = $state([]);
  let moodError = $state('');

  // Data query state
  let dataQuestion = $state('');
  let dataLoading = $state(false);
  let dataResult: DataQueryResponse | null = $state(null);
  let dataError = $state('');
  let showSql = $state(false);

  async function handleMoodSearch() {
    if (!moodQuery.trim() || moodLoading) return;
    moodLoading = true;
    moodError = '';
    moodResults = [];
    try {
      const res = await recommendMovies(moodQuery.trim());
      moodResults = res.movies;
    } catch (e) {
      moodError = e instanceof Error ? e.message : 'Something went wrong';
    } finally {
      moodLoading = false;
    }
  }

  async function handleDataQuery() {
    if (!dataQuestion.trim() || dataLoading) return;
    dataLoading = true;
    dataError = '';
    dataResult = null;
    try {
      dataResult = await queryData(dataQuestion.trim());
    } catch (e) {
      dataError = e instanceof Error ? e.message : 'Something went wrong';
    } finally {
      dataLoading = false;
    }
  }

  let chartData = $derived.by(() => {
    if (!dataResult?.rows.length || !dataResult.columns.length) return [];
    const cols = dataResult.columns;
    const labelCol = cols[0];
    const valueCol = cols.find((c, i) => i > 0 && dataResult!.rows.some(r => typeof r[c] === 'number'));
    if (!valueCol) return [];
    const items = dataResult.rows.slice(0, 15).map(r => ({
      label: String(r[labelCol] ?? ''),
      value: Number(r[valueCol] ?? 0),
    }));
    const max = Math.max(...items.map(i => i.value), 1);
    return items.map(i => ({ ...i, pct: (i.value / max) * 100 }));
  });
</script>

<div class="min-h-screen flex flex-col">
  <header class="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
    <div class="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">
      <Film class="w-7 h-7 text-primary" />
      <h1 class="text-xl font-bold tracking-tight">Movie Night</h1>
    </div>
  </header>

  <main class="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
    <div class="flex gap-1 mb-8 bg-muted rounded-lg p-1 w-fit">
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'mood' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}"
        onclick={() => (activeTab = 'mood')}
      >
        <Search class="w-4 h-4" />
        Mood Search
      </button>
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'data' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}"
        onclick={() => (activeTab = 'data')}
      >
        <Database class="w-4 h-4" />
        Data Query
      </button>
    </div>

    {#if activeTab === 'mood'}
      <section class="space-y-6">
        <form onsubmit={e => { e.preventDefault(); handleMoodSearch(); }} class="flex gap-3">
          <input
            type="text"
            bind:value={moodQuery}
            placeholder="Describe what you're in the mood for..."
            class="flex-1 px-4 py-2.5 rounded-lg bg-muted border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
          />
          <button
            type="submit"
            disabled={moodLoading || !moodQuery.trim()}
            class="px-5 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center gap-2"
          >
            {#if moodLoading}
              <span class="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            {:else}
              <Search class="w-4 h-4" />
            {/if}
            Search
          </button>
        </form>

        {#if moodError}
          <div class="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm">
            {moodError}
          </div>
        {/if}

        {#if moodLoading}
          <div class="flex items-center justify-center py-16 gap-3 text-muted-foreground">
            <span class="inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
            Finding movies for your mood...
          </div>
        {:else if moodResults.length}
          <div class="grid gap-4 sm:grid-cols-2">
            {#each moodResults as movie (movie.id)}
              <MovieCard {movie} />
            {/each}
          </div>
        {/if}
      </section>

    {:else}
      <section class="space-y-6">
        <form onsubmit={e => { e.preventDefault(); handleDataQuery(); }} class="flex gap-3">
          <input
            type="text"
            bind:value={dataQuestion}
            placeholder="Ask a data question about movies..."
            class="flex-1 px-4 py-2.5 rounded-lg bg-muted border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
          />
          <button
            type="submit"
            disabled={dataLoading || !dataQuestion.trim()}
            class="px-5 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center gap-2"
          >
            {#if dataLoading}
              <span class="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            {:else}
              <Database class="w-4 h-4" />
            {/if}
            Query
          </button>
        </form>

        {#if dataError}
          <div class="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm">
            {dataError}
          </div>
        {/if}

        {#if dataLoading}
          <div class="flex items-center justify-center py-16 gap-3 text-muted-foreground">
            <span class="inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
            Running your query...
          </div>
        {:else if dataResult}
          <div class="space-y-5">
            {#if dataResult.summary}
              <p class="text-muted-foreground text-sm leading-relaxed">{dataResult.summary}</p>
            {/if}

            <div>
              <button
                class="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
                onclick={() => (showSql = !showSql)}
              >
                <Database class="w-3 h-3" />
                {showSql ? 'Hide' : 'Show'} SQL
              </button>
              {#if showSql && dataResult.sql}
                <pre class="bg-muted rounded-lg p-4 text-xs text-foreground/80 overflow-x-auto border border-border font-mono">{dataResult.sql}</pre>
              {/if}
            </div>

            <DataTable columns={dataResult.columns} rows={dataResult.rows} />

            {#if chartData.length}
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <BarChart3 class="w-4 h-4" />
                  Chart
                </div>
                <div class="space-y-1.5">
                  {#each chartData as bar}
                    <div class="flex items-center gap-3 text-sm">
                      <span class="w-32 truncate text-right text-muted-foreground text-xs" title={bar.label}>
                        {bar.label}
                      </span>
                      <div class="flex-1 bg-muted rounded-full h-5 overflow-hidden">
                        <div
                          class="h-full bg-primary/70 rounded-full transition-all duration-500"
                          style="width: {bar.pct}%"
                        ></div>
                      </div>
                      <span class="w-16 text-xs text-muted-foreground text-right">
                        {typeof bar.value === 'number' && bar.value % 1 !== 0 ? bar.value.toFixed(1) : bar.value}
                      </span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      </section>
    {/if}
  </main>
</div>
