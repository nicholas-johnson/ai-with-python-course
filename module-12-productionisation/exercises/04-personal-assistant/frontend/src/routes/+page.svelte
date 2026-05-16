<script lang="ts">
	import { onMount } from 'svelte';
	import { MessageCircle, Calendar, Bell, Send, ChevronDown, ChevronRight } from 'lucide-svelte';
	import { streamChat, getCalendar, getReminders, type Message, type CalendarEvent, type Reminder, type ChatEvent } from '$lib/api';
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ActionCard from '$lib/components/ActionCard.svelte';
	import EventCard from '$lib/components/EventCard.svelte';

	type ChatItem =
		| { kind: 'message'; role: 'user' | 'assistant'; content: string; streaming?: boolean }
		| { kind: 'action'; actionType: string; description: string };

	let chatItems: ChatItem[] = $state([]);
	let inputText = $state('');
	let isStreaming = $state(false);
	let calendarEvents: CalendarEvent[] = $state([]);
	let reminders: Reminder[] = $state([]);
	let sidebarOpen = $state(true);
	let chatContainer: HTMLDivElement | undefined = $state();

	let messageHistory: Message[] = $derived(
		chatItems
			.filter((item): item is ChatItem & { kind: 'message' } => item.kind === 'message' && !item.streaming)
			.map(({ role, content }) => ({ role, content }))
	);

	function scrollToBottom() {
		if (chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
		}
	}

	async function loadSidebarData() {
		try {
			calendarEvents = await getCalendar();
		} catch {
			calendarEvents = [];
		}
		try {
			reminders = await getReminders();
		} catch {
			reminders = [];
		}
	}

	async function sendMessage() {
		const text = inputText.trim();
		if (!text || isStreaming) return;

		inputText = '';
		chatItems = [...chatItems, { kind: 'message', role: 'user', content: text }];
		isStreaming = true;

		let assistantText = '';
		chatItems = [...chatItems, { kind: 'message', role: 'assistant', content: '', streaming: true }];

		setTimeout(scrollToBottom, 0);

		try {
			for await (const event of streamChat(text, messageHistory.slice(0, -1))) {
				if (event.type === 'token') {
					assistantText += event.token;
					chatItems = chatItems.map((item, i) =>
						i === chatItems.length - 1 && item.kind === 'message'
							? { ...item, content: assistantText }
							: item
					);
					scrollToBottom();
				} else if (event.type === 'tool_call') {
					const desc = formatToolCall(event.data.name, event.data.arguments);
					chatItems = [
						...chatItems.slice(0, -1),
						{ kind: 'action', actionType: event.data.name, description: desc },
						chatItems[chatItems.length - 1],
					];
					scrollToBottom();
				} else if (event.type === 'done') {
					chatItems = chatItems.map((item, i) =>
						i === chatItems.length - 1 && item.kind === 'message'
							? { ...item, content: event.message.content || assistantText, streaming: false }
							: item
					);
				} else if (event.type === 'error') {
					chatItems = chatItems.map((item, i) =>
						i === chatItems.length - 1 && item.kind === 'message'
							? { ...item, content: `Sorry, something went wrong: ${event.error}`, streaming: false }
							: item
					);
				}
			}
		} catch (err) {
			chatItems = chatItems.map((item, i) =>
				i === chatItems.length - 1 && item.kind === 'message'
					? { ...item, content: 'Sorry, I couldn\'t connect to the server.', streaming: false }
					: item
			);
		}

		// Finalize streaming state
		chatItems = chatItems.map((item) =>
			item.kind === 'message' && item.streaming ? { ...item, streaming: false } : item
		);
		isStreaming = false;
		loadSidebarData();
	}

	function formatToolCall(name: string, args: Record<string, unknown>): string {
		if (name.includes('calendar') || name.includes('event')) {
			const title = (args.title as string) || (args.event as string) || 'event';
			return `Added to calendar: ${title}`;
		}
		if (name.includes('reminder')) {
			const title = (args.title as string) || (args.reminder as string) || 'reminder';
			return `Set reminder: ${title}`;
		}
		if (name.includes('note') || name.includes('search')) {
			const query = (args.query as string) || (args.q as string) || '';
			return `Searched notes${query ? `: "${query}"` : ''}`;
		}
		return `Ran: ${name}`;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	onMount(() => {
		loadSidebarData();
	});
</script>

<div class="flex h-screen overflow-hidden">
	<!-- Sidebar -->
	<aside class="w-72 border-r border-border bg-card flex flex-col {sidebarOpen ? '' : 'hidden'} lg:flex">
		<div class="p-5 border-b border-border">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
					<span class="text-primary-foreground font-bold text-lg">C</span>
				</div>
				<div>
					<h1 class="font-semibold text-foreground">Compass</h1>
					<p class="text-xs text-muted-foreground">Personal Assistant</p>
				</div>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto p-4 space-y-5">
			<!-- Calendar Section -->
			<section>
				<div class="flex items-center gap-2 mb-2">
					<Calendar class="w-4 h-4 text-primary" />
					<h2 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Upcoming</h2>
				</div>
				{#if calendarEvents.length > 0}
					<div class="space-y-1">
						{#each calendarEvents.slice(0, 3) as event}
							<EventCard {event} />
						{/each}
					</div>
				{:else}
					<p class="text-xs text-muted-foreground pl-6">No upcoming events</p>
				{/if}
			</section>

			<!-- Reminders Section -->
			<section>
				<div class="flex items-center gap-2 mb-2">
					<Bell class="w-4 h-4 text-primary" />
					<h2 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Reminders</h2>
				</div>
				{#if reminders.length > 0}
					<div class="space-y-1">
						{#each reminders as reminder}
							<div class="flex items-start gap-2.5 px-3 py-2 rounded-md hover:bg-muted/60 transition-colors">
								<Bell class="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
								<div class="flex-1 min-w-0">
									<p class="text-sm font-medium text-foreground truncate">{reminder.title}</p>
									{#if reminder.due}
										<p class="text-xs text-muted-foreground">{reminder.due}</p>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="text-xs text-muted-foreground pl-6">No active reminders</p>
				{/if}
			</section>
		</div>
	</aside>

	<!-- Chat Area -->
	<main class="flex-1 flex flex-col">
		<!-- Header -->
		<header class="px-5 py-3 border-b border-border bg-card flex items-center gap-3">
			<button
				class="lg:hidden p-1.5 rounded-md hover:bg-muted transition-colors"
				onclick={() => sidebarOpen = !sidebarOpen}
			>
				{#if sidebarOpen}
					<ChevronDown class="w-5 h-5" />
				{:else}
					<ChevronRight class="w-5 h-5" />
				{/if}
			</button>
			<MessageCircle class="w-5 h-5 text-primary" />
			<h2 class="font-medium text-foreground">Chat with Compass</h2>
		</header>

		<!-- Messages -->
		<div bind:this={chatContainer} class="flex-1 overflow-y-auto px-5 py-6 space-y-4">
			{#if chatItems.length === 0}
				<div class="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
					<div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
						<div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
							<span class="text-primary-foreground font-bold text-xl">C</span>
						</div>
					</div>
					<h3 class="text-lg font-semibold text-foreground mb-2">Hey! I'm Compass, your personal assistant.</h3>
					<p class="text-sm text-muted-foreground">Ask me anything, or tell me to manage your calendar and reminders.</p>
				</div>
			{:else}
				{#each chatItems as item}
					{#if item.kind === 'message'}
						<ChatMessage role={item.role} content={item.content} streaming={item.streaming ?? false} />
					{:else if item.kind === 'action'}
						<ActionCard actionType={item.actionType} description={item.description} />
					{/if}
				{/each}
			{/if}
		</div>

		<!-- Input -->
		<div class="border-t border-border bg-card px-5 py-4">
			<div class="flex items-end gap-3 max-w-3xl mx-auto">
				<textarea
					class="flex-1 resize-none rounded-xl border border-border bg-background px-4 py-3 text-sm
						placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30
						focus:border-primary transition-all min-h-[44px] max-h-[120px]"
					placeholder="Ask Compass anything..."
					rows="1"
					bind:value={inputText}
					onkeydown={handleKeydown}
					disabled={isStreaming}
				></textarea>
				<button
					class="flex-shrink-0 w-10 h-10 rounded-xl bg-primary text-primary-foreground
						flex items-center justify-center hover:opacity-90 transition-opacity
						disabled:opacity-40 disabled:cursor-not-allowed"
					onclick={sendMessage}
					disabled={!inputText.trim() || isStreaming}
				>
					<Send class="w-4 h-4" />
				</button>
			</div>
		</div>
	</main>
</div>
