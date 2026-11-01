<script lang="ts">
  let { columns, rows }: { columns: string[]; rows: Record<string, unknown>[] } = $props();
</script>

{#if columns.length && rows.length}
  <div class="overflow-x-auto rounded-lg border border-border">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-muted/50">
          {#each columns as col}
            <th class="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {col}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row, i}
          <tr class={i % 2 === 0 ? 'bg-card' : 'bg-muted/20'}>
            {#each columns as col}
              <td class="px-4 py-2 text-foreground whitespace-nowrap">
                {row[col] ?? '—'}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{:else}
  <p class="text-muted-foreground text-sm text-center py-6">No data to display.</p>
{/if}
