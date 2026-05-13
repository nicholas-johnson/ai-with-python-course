<script lang="ts">
	import { streamChat, analyseImage, transcribeAudio, checkHealth, type Message, type ToolCall, type ToolResult } from '$lib/api';
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ToolCallCard from '$lib/components/ToolCallCard.svelte';
	import { Search, ImagePlus, Mic, Send, Loader2, Wifi, WifiOff } from 'lucide-svelte';

	type ChatItem =
		| { kind: 'message'; message: Message }
		| { kind: 'tool_call'; data: ToolCall }
		| { kind: 'tool_result'; data: ToolResult }
		| { kind: 'image_analysis'; image: string; description: string }
		| { kind: 'transcript'; text: string };

	let items: ChatItem[] = $state([]);
	let messages: Message[] = $state([]);
	let input = $state('');
	let streaming = $state(false);
	let connected = $state(false);
	let scrollContainer: HTMLElement;

	$effect(() => {
		checkHealth().then((ok) => (connected = ok));
		const interval = setInterval(() => checkHealth().then((ok) => (connected = ok)), 5000);
		return () => clearInterval(interval);
	});

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

	async function handleImageUpload() {
		const fileInput = document.createElement('input');
		fileInput.type = 'file';
		fileInput.accept = 'image/*';
		fileInput.onchange = async () => {
			const file = fileInput.files?.[0];
			if (!file) return;

			const reader = new FileReader();
			reader.onload = async () => {
				const base64 = (reader.result as string).split(',')[1];
				const dataUrl = reader.result as string;

				items = [
					...items,
					{ kind: 'message', message: { role: 'user', content: '📷 Uploaded an image for analysis' } },
				];
				scrollToBottom();

				try {
					const result = await analyseImage(base64, input || 'Describe and analyse this image in detail.');
					items = [
						...items,
						{ kind: 'image_analysis', image: dataUrl, description: result.description },
					];
					const assistantMsg: Message = { role: 'assistant', content: result.description };
					messages = [...messages, { role: 'user', content: 'Analyse this image.' }, assistantMsg];
				} catch (err) {
					items = [
						...items,
						{ kind: 'message', message: { role: 'assistant', content: `Vision error: ${err}` } },
					];
				}
				scrollToBottom();
			};
			reader.readAsDataURL(file);
		};
		fileInput.click();
	}

	async function handleAudioUpload() {
		const fileInput = document.createElement('input');
		fileInput.type = 'file';
		fileInput.accept = 'audio/*';
		fileInput.onchange = async () => {
			const file = fileInput.files?.[0];
			if (!file) return;

			items = [
				...items,
				{ kind: 'message', message: { role: 'user', content: `🎤 Uploaded audio: ${file.name}` } },
			];
			scrollToBottom();

			try {
				const result = await transcribeAudio(file);
				items = [...items, { kind: 'transcript', text: result.transcript }];
				const assistantMsg: Message = { role: 'assistant', content: `Transcript: ${result.transcript}` };
				messages = [...messages, assistantMsg];
			} catch (err) {
				items = [
					...items,
					{ kind: 'message', message: { role: 'assistant', content: `Transcription error: ${err}` } },
				];
			}
			scrollToBottom();
		};
		fileInput.click();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}
</script>

<div class="flex flex-col h-screen max-w-4xl mx-auto">
	<!-- Header -->
	<header class="flex items-center justify-between border-b px-6 py-4">
		<div class="flex items-center gap-3">
			<Search class="h-6 w-6 text-primary" />
			<h1 class="text-xl font-semibold">Research Assistant</h1>
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
				<Search class="h-12 w-12 mb-4 opacity-30" />
				<p class="text-lg font-medium">What would you like to research?</p>
				<p class="text-sm mt-1">Chat, upload images, or transcribe audio.</p>
			</div>
		{/if}

		{#each items as item}
			{#if item.kind === 'message'}
				<ChatMessage message={item.message} />
			{:else if item.kind === 'tool_call'}
				<ToolCallCard type="call" name={item.data.name} content={JSON.stringify(item.data.arguments, null, 2)} />
			{:else if item.kind === 'tool_result'}
				<ToolCallCard type="result" name={item.data.name} content={item.data.content} />
			{:else if item.kind === 'image_analysis'}
				<div class="flex gap-3">
					<img src={item.image} alt="Uploaded" class="w-48 h-48 object-cover rounded-lg border" />
					<div class="bg-muted rounded-lg p-4 flex-1">
						<p class="text-sm font-medium mb-1">Image Analysis</p>
						<p class="text-sm text-muted-foreground">{item.description}</p>
					</div>
				</div>
			{:else if item.kind === 'transcript'}
				<div class="bg-muted rounded-lg p-4">
					<p class="text-sm font-medium mb-1">Transcript</p>
					<p class="text-sm text-muted-foreground">{item.text}</p>
				</div>
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
			<button
				onclick={handleImageUpload}
				class="flex items-center justify-center h-10 w-10 rounded-md border bg-background hover:bg-accent transition-colors"
				title="Upload image"
			>
				<ImagePlus class="h-4 w-4" />
			</button>
			<button
				onclick={handleAudioUpload}
				class="flex items-center justify-center h-10 w-10 rounded-md border bg-background hover:bg-accent transition-colors"
				title="Upload audio"
			>
				<Mic class="h-4 w-4" />
			</button>
			<textarea
				bind:value={input}
				onkeydown={handleKeydown}
				placeholder="Ask anything... (Enter to send)"
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
</div>
