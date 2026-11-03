<script lang="ts">
	import {
		streamChat,
		generatePlan,
		getPreferences,
		checkHealth,
		type Message,
		type PlanStep,
		type ToolCall,
		type ToolResult,
	} from '$lib/api';
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ToolCallCard from '$lib/components/ToolCallCard.svelte';
	import PlanStepComponent from '$lib/components/PlanStep.svelte';
	import { Plane, Send, Loader2, Wifi, WifiOff, ListChecks, Settings } from 'lucide-svelte';

	type ChatItem =
		| { kind: 'message'; message: Message }
		| { kind: 'tool_call'; data: ToolCall }
		| { kind: 'tool_result'; data: ToolResult };

	let items: ChatItem[] = $state([]);
	let messages: Message[] = $state([]);
	let input = $state('');
	let streaming = $state(false);
	let connected = $state(false);
	let planSteps: PlanStep[] = $state([]);
	let planLoading = $state(false);
	let preferences: Record<string, string> = $state({});
	let scrollContainer: HTMLElement;

	$effect(() => {
		checkHealth().then((ok) => (connected = ok));
		const interval = setInterval(() => checkHealth().then((ok) => (connected = ok)), 5000);
		return () => clearInterval(interval);
	});

	$effect(() => {
		getPreferences().then((prefs) => (preferences = prefs));
		const interval = setInterval(() => getPreferences().then((prefs) => (preferences = prefs)), 8000);
		return () => clearInterval(interval);
	});

	const preferenceEntries = $derived(Object.entries(preferences));

	function scrollToBottom() {
		requestAnimationFrame(() => {
			if (scrollContainer) scrollContainer.scrollTop = scrollContainer.scrollHeight;
		});
	}

	async function sendMessage() {
		const text = input.trim();
		if (!text || streaming) return;
		input = '';

		const userMsg: Message = { role: 'user', content: text };
		messages = [...messages, userMsg];
		items = [...items, { kind: 'message', message: userMsg }];
		scrollToBottom();

		streaming = true;
		let assistantContent = '';
		items = [...items, { kind: 'message', message: { role: 'assistant', content: '' } }];

		try {
			for await (const event of streamChat(messages)) {
				if (event.type === 'token') {
					assistantContent += event.token;
					items[items.length - 1] = {
						kind: 'message',
						message: { role: 'assistant', content: assistantContent },
					};
					scrollToBottom();
				} else if (event.type === 'plan_step') {
					const idx = planSteps.findIndex((s) => s.number === event.data.number);
					if (idx >= 0) {
						planSteps[idx] = event.data;
						planSteps = [...planSteps];
					} else {
						planSteps = [...planSteps, event.data];
					}
				} else if (event.type === 'tool_call') {
					items.splice(items.length - 1, 0, { kind: 'tool_call', data: event.data });
					items = [...items];
					scrollToBottom();
				} else if (event.type === 'tool_result') {
					items.splice(items.length - 1, 0, { kind: 'tool_result', data: event.data });
					items = [...items];
					scrollToBottom();
				} else if (event.type === 'done') {
					const assistantMsg = event.message;
					messages = [...messages, assistantMsg];
					items[items.length - 1] = { kind: 'message', message: assistantMsg };
					getPreferences().then((prefs) => (preferences = prefs));
				} else if (event.type === 'error') {
					items[items.length - 1] = {
						kind: 'message',
						message: { role: 'assistant', content: `Error: ${event.error}` },
					};
				}
			}
		} catch (err) {
			items[items.length - 1] = {
				kind: 'message',
				message: { role: 'assistant', content: `Connection error: ${err}` },
			};
		}
		streaming = false;
		scrollToBottom();
	}

	async function handleGeneratePlan() {
		if (planLoading) return;
		const lastUserMsg = messages.filter((m) => m.role === 'user').pop();
		const prompt = lastUserMsg?.content ?? 'Plan a holiday';
		planLoading = true;
		try {
			planSteps = await generatePlan(prompt);
		} catch (err) {
			planSteps = [{ number: 1, description: `Failed to generate plan: ${err}`, status: 'failed', result: null }];
		}
		planLoading = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}
</script>

<div class="flex h-screen">
	<!-- Left Sidebar: Plan -->
	<aside class="w-64 border-r flex flex-col shrink-0">
		<div class="flex items-center gap-2 px-4 py-4 border-b">
			<ListChecks class="h-5 w-5 text-primary" />
			<h2 class="font-semibold text-sm">Plan</h2>
		</div>
		<div class="flex-1 overflow-y-auto px-3 py-3">
			{#if planSteps.length === 0}
				<p class="text-xs text-muted-foreground leading-relaxed">
					No plan yet — start chatting to generate one.
				</p>
			{:else}
				<div class="space-y-1">
					{#each planSteps as step}
						<PlanStepComponent {step} />
					{/each}
				</div>
			{/if}
		</div>
		<div class="px-3 py-3 border-t">
			<button
				onclick={handleGeneratePlan}
				disabled={planLoading}
				class="w-full flex items-center justify-center gap-2 rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
			>
				{#if planLoading}
					<Loader2 class="h-4 w-4 animate-spin" />
					Generating...
				{:else}
					<ListChecks class="h-4 w-4" />
					Generate Plan
				{/if}
			</button>
		</div>
	</aside>

	<!-- Center: Chat -->
	<main class="flex-1 flex flex-col min-w-0">
		<!-- Header -->
		<header class="flex items-center justify-between border-b px-6 py-4">
			<div class="flex items-center gap-3">
				<Plane class="h-6 w-6 text-primary" />
				<h1 class="text-xl font-semibold">Holiday Planner</h1>
			</div>
			<div class="flex items-center gap-2 text-sm">
				{#if connected}
					<Wifi class="h-4 w-4 text-green-500" />
					<span class="text-muted-foreground">Connected</span>
				{:else}
					<WifiOff class="h-4 w-4 text-destructive" />
					<span class="text-destructive">Disconnected</span>
				{/if}
			</div>
		</header>

		<!-- Messages -->
		<div bind:this={scrollContainer} class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
			{#if items.length === 0}
				<div class="flex flex-col items-center justify-center h-full text-muted-foreground">
					<Plane class="h-12 w-12 mb-4 opacity-30" />
					<p class="text-lg font-medium">Where would you like to go?</p>
					<p class="text-sm mt-1">Tell me about your dream holiday and I'll help plan it.</p>
				</div>
			{/if}

			{#each items as item}
				{#if item.kind === 'message'}
					<ChatMessage message={item.message} />
				{:else if item.kind === 'tool_call'}
					<ToolCallCard type="call" name={item.data.name} content={JSON.stringify(item.data.arguments, null, 2)} />
				{:else if item.kind === 'tool_result'}
					<ToolCallCard type="result" name={item.data.name} content={item.data.content} />
				{/if}
			{/each}

			{#if streaming}
				<div class="flex items-center gap-2 text-muted-foreground text-sm">
					<Loader2 class="h-4 w-4 animate-spin" />
					<span>Thinking...</span>
				</div>
			{/if}
		</div>

		<!-- Input bar -->
		<div class="border-t px-6 py-4">
			<div class="flex items-end gap-2">
				<textarea
					bind:value={input}
					onkeydown={handleKeydown}
					placeholder="Plan a trip to Japan for 2 weeks..."
					rows={1}
					class="flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
				></textarea>
				<button
					onclick={sendMessage}
					disabled={streaming || !input.trim()}
					class="flex items-center justify-center h-10 w-10 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
					title="Send"
				>
					<Send class="h-4 w-4" />
				</button>
			</div>
		</div>
	</main>

	<!-- Right Sidebar: Preferences -->
	<aside class="w-56 border-l flex flex-col shrink-0">
		<div class="flex items-center gap-2 px-4 py-4 border-b">
			<Settings class="h-5 w-5 text-primary" />
			<h2 class="font-semibold text-sm">Preferences</h2>
		</div>
		<div class="flex-1 overflow-y-auto px-3 py-3">
			{#if preferenceEntries.length === 0}
				<p class="text-xs text-muted-foreground leading-relaxed">
					No preferences saved yet.
				</p>
			{:else}
				<dl class="space-y-3">
					{#each preferenceEntries as [key, value]}
						<div>
							<dt class="text-xs font-medium text-muted-foreground uppercase tracking-wide">{key}</dt>
							<dd class="text-sm mt-0.5">{value}</dd>
						</div>
					{/each}
				</dl>
			{/if}
		</div>
	</aside>
</div>
